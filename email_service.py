import smtplib
from email.message import EmailMessage
from datetime import datetime
from email_config import SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL, SMTP_SERVER, SMTP_PORT
from menu import MENU


def send_order_email(order_number, customer, items, total):
    if "YOUR_SENDER_EMAIL" in SENDER_EMAIL or "YOUR_16_CHARACTER" in SENDER_PASSWORD:
        print("Email not configured. Order was still completed in the application.")
        return False

    lines = [
        f"NEW CAFÉ ORDER #{order_number}",
        "=" * 35,
        "",
        f"Customer Name: {customer.get('name', '')}",
        f"Phone: {customer.get('phone', '')}",
        f"Order Type: {customer.get('order_type', '')}",
        f"Address: {customer.get('address', 'N/A')}",
        f"Order Time: {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
        "",
        "ORDER DETAILS",
        "-" * 35
    ]

    for item in items:
        name = item["item"]
        qty = item["quantity"]
        price = next(
            foods[name]["price"]
            for foods in MENU.values()
            if name in foods
        )
        lines.append(f"{qty} x {name} = Rs.{price * qty}")

    lines += [
        "",
        f"TOTAL: Rs.{total}",
        "",
        "Please prepare the order.",
        "This notification was generated automatically by Cafe Delight."
    ]

    msg = EmailMessage()
    msg["Subject"] = f"New Cafe Order #{order_number}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.set_content("\n".join(lines))

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=15) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as exc:
        print("Email error:", exc)
        return False