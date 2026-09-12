from flask import Flask, render_template, request, jsonify, session
from datetime import datetime
import random
import json

from chatbot import CafeChatbot
from menu import MENU
from email_service import send_order_email
from models import db, PlacedOrder

app = Flask(__name__)
app.secret_key = "change_this_to_something_random"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafe.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


def get_state():
    if "current_order" not in session:
        session["current_order"] = []
    if "customer" not in session:
        session["customer"] = {}
    if "bot_state" not in session:
        session["bot_state"] = None
    if "pending_item" not in session:
        session["pending_item"] = None
    if "order_number" not in session:
        session["order_number"] = random.randint(1000, 9999)
    if "awaiting_confirmation" not in session:
        session["awaiting_confirmation"] = False
    if "pending_total" not in session:
        session["pending_total"] = 0


def get_bot():
    bot = CafeChatbot(MENU)
    bot.state = session.get("bot_state")
    bot.pending_item = session.get("pending_item")
    return bot


def save_bot(bot):
    session["bot_state"] = bot.state
    session["pending_item"] = bot.pending_item
    session.modified = True


def cart_summary():
    current_order = session.get("current_order", [])
    lines = []
    total = 0
    total_items = 0
    bot = CafeChatbot(MENU)

    for order in current_order:
        price = bot.get_price(order["item"])
        amount = price * order["quantity"]
        total += amount
        total_items += order["quantity"]
        lines.append({"item": order["item"], "quantity": order["quantity"], "amount": amount})

    return {"lines": lines, "total": total, "total_items": total_items}


def checkout_flow(bot):
    current_order = session.get("current_order", [])
    customer = session.get("customer", {})

    if not current_order:
        return {"message": "Your cart is empty, so there is nothing to place."}

    total = sum(bot.get_price(x["item"]) * x["quantity"] for x in current_order)

    if not customer.get("name"):
        bot.state = "name"
        save_bot(bot)
        return {"message": "Before I place your order, may I have your name?"}

    if not customer.get("phone"):
        bot.state = "phone"
        save_bot(bot)
        return {"message": "Please provide your phone number."}

    if not customer.get("order_type"):
        bot.state = "order_type"
        save_bot(bot)
        return {
            "message":
            "How would you like to receive your order?\n\nDine-in\nTakeaway\nDelivery"
        }

    if customer.get("order_type") == "Delivery" and not customer.get("address"):
        bot.state = "address"
        save_bot(bot)
        return {"message": "Please provide your complete delivery address."}

    # All details collected -> build summary, wait for confirm/cancel
    order_number = session["order_number"]
    lines = [f"ORDER #{order_number}", "", "ITEMS:"]
    for order in current_order:
        amount = bot.get_price(order["item"]) * order["quantity"]
        lines.append(f"{order['quantity']} x {order['item']} - Rs. {amount}")
    lines += [
        "",
        f"TOTAL: Rs. {total}",
        "",
        f"Name: {customer.get('name', '')}",
        f"Phone: {customer.get('phone', '')}",
        f"Type: {customer.get('order_type', '')}"
    ]
    if customer.get("address"):
        lines.append(f"Address: {customer['address']}")

    lines.append("\nType 'confirm' to place this order, or 'cancel' to go back.")

    session["awaiting_confirmation"] = True
    session["pending_total"] = total
    session.modified = True

    return {"message": "\n".join(lines)}


def finalize_order():
    current_order = session.get("current_order", [])
    customer = session.get("customer", {})
    total = session.get("pending_total", 0)
    order_number = session["order_number"]

    email_ok = send_order_email(
        order_number=order_number,
        customer=customer,
        items=current_order,
        total=total
    )

    placed = PlacedOrder(
        order_number=order_number,
        name=customer.get("name", ""),
        phone=customer.get("phone", ""),
        order_type=customer.get("order_type", ""),
        address=customer.get("address"),
        items_json=json.dumps(current_order),
        total=total,
        email_sent=email_ok
    )
    db.session.add(placed)
    db.session.commit()

    if email_ok:
        message = (
            "ORDER CONFIRMED!\n\n"
            f"Order Number: #{order_number}\n"
            f"Total: Rs. {total}\n\n"
            "The cafe has received your order notification by email.\n\n"
            "Thank you for ordering from Cafe Delight!"
        )
    else:
        message = (
            "ORDER CONFIRMED!\n\n"
            f"Order Number: #{order_number}\n"
            f"Total: Rs. {total}\n\n"
            "The order was completed, but the email notification could not be sent.\n\n"
            "Please check your email configuration."
        )

    # reset session state for next order
    session["current_order"] = []
    session["customer"] = {}
    session["bot_state"] = None
    session["pending_item"] = None
    session["awaiting_confirmation"] = False
    session["pending_total"] = 0
    session["order_number"] = random.randint(1000, 9999)
    session.modified = True

    return message


@app.route("/")
def index():
    get_state()
    return jsonify({
        "status": "Cafe Delight API Server Running",
        "message": "Please access the frontend UI via Vite at http://localhost:8443"
    })



@app.route("/api/chat", methods=["POST"])
def chat():
    get_state()
    text = request.json.get("message", "").strip()

    if not text:
        return jsonify({"message": "", "cart": cart_summary()})

    # Handle the confirm/cancel step (was a popup dialog in the Tkinter version)
    if session.get("awaiting_confirmation"):
        low = text.lower().strip()
        if low in ("confirm", "yes", "y", "place order"):
            message = finalize_order()
            return jsonify({"message": message, "cart": cart_summary()})
        elif low in ("cancel", "no", "n"):
            session["awaiting_confirmation"] = False
            session["pending_total"] = 0
            session.modified = True
            return jsonify({
                "message": "No problem.\n\nYour order has not been placed.",
                "cart": cart_summary()
            })
        else:
            return jsonify({
                "message": "Please type 'confirm' to place the order, or 'cancel' to go back.",
                "cart": cart_summary()
            })

    bot = get_bot()
    current_order = session.get("current_order", [])
    customer = session.get("customer", {})

    response = bot.process(text, current_order, customer)
    session["customer"] = customer
    save_bot(bot)

    action = response.get("action")

    if action == "add_item":
        item = response["item"]
        qty = response["quantity"]
        found = False
        for order in current_order:
            if order["item"] == item:
                order["quantity"] += qty
                found = True
                break
        if not found:
            current_order.append({"item": item, "quantity": qty})
        session["current_order"] = current_order
        session.modified = True
        return jsonify({"message": response["message"], "cart": cart_summary()})

    if action == "remove_item":
        name = response["item"]
        session["current_order"] = [x for x in current_order if x["item"] != name]
        session.modified = True
        return jsonify({"message": response["message"], "cart": cart_summary()})

    if action == "set_customer":
        return jsonify({"message": response["message"], "cart": cart_summary()})

    if action == "checkout":
        result = checkout_flow(bot)
        return jsonify({"message": result["message"], "cart": cart_summary()})

    return jsonify({"message": response["message"], "cart": cart_summary()})


@app.route("/api/cart/view", methods=["POST"])
def view_cart():
    get_state()
    summary = cart_summary()
    if not summary["lines"]:
        return jsonify({
            "message": "Your cart is currently empty.\n\nWould you like to see our menu?",
            "cart": summary
        })

    lines = ["YOUR CURRENT ORDER", ""]
    for line in summary["lines"]:
        lines.append(f"{line['quantity']} x {line['item']} = Rs. {line['amount']}")
    lines.append(f"\nTOTAL: Rs. {summary['total']}")

    return jsonify({"message": "\n".join(lines), "cart": summary})


@app.route("/api/cart/clear", methods=["POST"])
def clear_cart():
    get_state()
    session["current_order"] = []
    session["customer"] = {}
    session["bot_state"] = None
    session["pending_item"] = None
    session["awaiting_confirmation"] = False
    session["pending_total"] = 0
    session.modified = True

    return jsonify({
        "message": "Your order has been cleared.\n\nWhat would you like to have?",
        "cart": cart_summary()
    })


@app.route("/api/cart/summary")
def cart_summary_route():
    get_state()
    return jsonify(cart_summary())


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)