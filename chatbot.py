import re


class CafeChatbot:

    def __init__(self, menu):
        self.menu = menu
        self.state = None
        self.pending_item = None

    def reset(self):
        self.state = None
        self.pending_item = None

    def all_items(self):
        items = {}
        for category, foods in self.menu.items():
            for name, data in foods.items():
                items[name.lower()] = (name, data, category)
        return items

    def find_item(self, text):
        low = text.lower()

        # Direct exact match or substring match
        for key, value in self.all_items().items():
            if key in low:
                return value

        # Word intersection fallback
        words = set(re.findall(r"[a-z]+", low))
        best = None
        best_score = 0

        for key, value in self.all_items().items():
            item_words = set(key.split())
            score = len(words.intersection(item_words))
            if score > best_score:
                best_score = score
                best = value

        if best_score > 0:
            return best
        return None

    def get_price(self, item_name):
        for foods in self.menu.values():
            if item_name in foods:
                return foods[item_name]["price"]
        return 0

    def menu_text(self):
        lines = ["OUR MENU", ""]
        for category, foods in self.menu.items():
            lines.append(f"{category}")
            for name, data in foods.items():
                lines.append(f"• {name} - Rs. {data['price']}")
            lines.append("")
        return "\n".join(lines).strip()

    def item_info(self, item):
        name, data, category = item
        return (
            f"{name} — Rs. {data['price']}\n"
            f"Category: {category}\n\n"
            f"{data['description']}"
        )

    def is_yes(self, text):
        low = text.lower().strip()
        yes_words = [
            "yes", "y", "yeah", "yep", "yup", "sure", "okay", "ok",
            "of course", "definitely", "please", "i do", "i want it",
            "yes please", "sure thing", "i'll have one", "i want to order it",
            "i want this", "add it", "start order", "let's order", "i want to order"
        ]
        return low in yes_words or any(w in low for w in ["yes please", "i want it", "i'll have one", "order it", "want to order"])

    def is_no(self, text):
        low = text.lower().strip()
        no_words = ["no", "n", "nope", "nah", "not now", "no thanks", "no thank you"]
        return low in no_words

    def is_done_with_order(self, text):
        low = text.lower().strip()
        phrases = [
            "no", "nope", "nothing else", "nothing more", "that's all",
            "thats all", "that is all", "just that", "only that", "no more",
            "no thanks", "no thank you", "nothing", "done", "finish",
            "that's it", "thats it", "just this", "only this"
        ]
        return low in phrases

    def process(self, text, current_order, customer):
        low = text.lower().strip()

        # ── STATE 1: ITEM CONFIRMATION (e.g. after querying a specific item price) ──
        if self.state == "item_confirmation":
            if self.is_yes(low):
                item = self.pending_item
                self.state = "quantity"
                return {
                    "message":
                    f"Great choice!\n\n"
                    f"{item} costs Rs. {self.get_price(item)}.\n\n"
                    f"How many would you like?"
                }
            if self.is_no(low):
                self.state = "ordering" if current_order else None
                self.pending_item = None
                prompt = "What else would you like to add?" if current_order else "Would you like to see something else from the menu?"
                return {"message": f"No problem.\n\n{prompt}"}

        # ── STATE 2: QUANTITY SELECTION ──
        if self.state == "quantity":
            try:
                match = re.search(r"\d+", low)
                if not match:
                    words_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "a": 1, "an": 1}
                    qty = 0
                    for w, val in words_num.items():
                        if w in low.split():
                            qty = val
                            break
                    if qty == 0:
                        raise ValueError
                else:
                    qty = int(match.group())
                if qty <= 0 or qty > 50:
                    raise ValueError
            except (AttributeError, ValueError):
                return {
                    "message": "Please enter a valid quantity.\n\nFor example: 1, 2, 3..."
                }

            item = self.pending_item
            self.state = "ordering"  # Keep in ORDERING mode so subsequent prompt asks "What else would you like to add?"
            self.pending_item = None

            return {
                "action": "add_item",
                "item": item,
                "quantity": qty,
                "message":
                f"Added {qty} x {item} to your cart.\n\nWhat else would you like to add?"
            }

        # ── STATE 3: OFFERED ORDER (User was asked "Would you like to order something?") ──
        if self.state == "offered_order":
            if self.is_yes(low):
                self.state = "ordering"
                return {"message": "Sure! What would you like to order?"}
            if self.is_no(low):
                self.state = None
                return {"message": "No problem! Let me know if you need anything else."}

        # ── STATE 4: ORDERING MODE ──
        if self.state == "ordering":
            # If user explicitly wants to checkout:
            if any(x in low for x in ["checkout", "place order", "confirm order", "finish order", "complete order", "order now"]):
                return {"action": "checkout", "message": ""}

            # If user says done with ordering:
            if self.is_done_with_order(low):
                self.state = None
                if current_order:
                    return {"message": "Great! Say 'checkout' whenever you are ready to place your order."}
                return {"message": "Your cart is currently empty. Let me know whenever you'd like to order!"}

            # Check if user names an item directly in ordering mode:
            item = self.find_item(low)
            if item:
                self.pending_item = item[0]
                self.state = "quantity"
                return {
                    "message": f"{item[0]} — Rs. {self.get_price(item[0])}.\n\nHow many would you like?"
                }

        # ── CHECKOUT STATES (Name, Phone, Order Type, Address) ──
        if self.state == "name":
            if len(text.strip()) < 2:
                return {"message": "Please enter your name."}

            customer["name"] = text.strip()
            self.state = "phone"
            return {
                "action": "set_customer",
                "field": "name",
                "value": text.strip(),
                "message": f"Nice to meet you, {text.strip()}!\n\nNow please provide your phone number."
            }

        if self.state == "phone":
            if not re.fullmatch(r"[\d\s+\-()]{7,20}", text):
                return {"message": "Please enter a valid phone number."}

            customer["phone"] = text.strip()
            self.state = "order_type"
            return {
                "action": "set_customer",
                "field": "phone",
                "value": text.strip(),
                "message": "Will this be Dine-in, Takeaway, or Delivery?"
            }

        if self.state == "order_type":
            if "dine" in low:
                value = "Dine-in"
            elif "take" in low or "pickup" in low or "pick up" in low:
                value = "Takeaway"
            elif "deliver" in low:
                value = "Delivery"
            else:
                return {"message": "Please choose one:\n\nDine-in\nTakeaway\nDelivery"}

            customer["order_type"] = value
            if value == "Delivery":
                self.state = "address"
                return {
                    "action": "set_customer",
                    "field": "order_type",
                    "value": value,
                    "message": "Delivery selected.\n\nPlease enter your complete delivery address."
                }

            self.state = None
            return {
                "action": "set_customer",
                "field": "order_type",
                "value": value,
                "message": f"{value} selected.\n\nSay 'checkout' whenever you are ready."
            }

        if self.state == "address":
            if len(text.strip()) < 5:
                return {"message": "Please provide a complete delivery address."}

            customer["address"] = text.strip()
            self.state = None
            return {
                "action": "set_customer",
                "field": "address",
                "value": text.strip(),
                "message": "Delivery address saved successfully.\n\nSay 'checkout' when you are ready to place the order."
            }

        # ── INTENTS & GENERAL QUERIES ──

        # 1. Direct Order Intent
        if any(w in low for w in [
            "i want to order", "i'd like to order", "id like to order", "i would like to order",
            "start order", "start new order", "let's order", "lets order", "can i order",
            "want to order"
        ]):
            self.state = "ordering"
            return {"message": "Sure! What would you like to order?"}

        # 2. Checkout Intent
        if any(x in low for x in [
            "checkout", "place order", "confirm order", "finish order",
            "complete order", "order now"
        ]):
            return {"action": "checkout", "message": ""}

        # 3. Opening Hours
        if any(w in low for w in [
            "opening hour", "opening hours", "business hour", "business hours",
            "restaurant hour", "restaurant hours", "what time do you open",
            "what time do you close", "when do you open", "when do you close",
            "when are you open", "are you open", "open today", "operating hours",
            "hours", "timing", "timings", "working hours", "open time", "close time",
            "schedule"
        ]):
            if self.state != "ordering":
                self.state = "offered_order"
            prompt = "What would you like to add to your order?" if self.state == "ordering" else "Would you like to order something?"
            return {
                "message":
                "Cafe Delight Opening Hours:\n\n"
                "• Monday – Sunday: 10:00 AM – 10:00 PM\n\n"
                f"{prompt}"
            }

        # 4. Greetings
        if any(x in low for x in ["hello", "hi", "hey", "namaste", "greetings"]):
            if self.state != "ordering":
                self.state = "offered_order"
            return {
                "message":
                "Hello!\n\nWelcome to Cafe Delight.\nWould you like to see our menu or place an order?"
            }

        # 5. Popular Items / Recommendations
        if any(w in low for w in [
            "popular", "best seller", "bestseller", "recommend", "special",
            "today's special", "todays special", "top item", "favorite", "favourite",
            "best items", "what is popular"
        ]):
            if self.state != "ordering":
                self.state = "offered_order"
            prompt = "What would you like to add to your order?" if self.state == "ordering" else "Would you like to order one of these?"
            return {
                "message":
                "Here are our most popular customer favorites:\n\n"
                "• Chicken Burger - Rs. 180\n"
                "• Margherita Pizza - Rs. 220\n"
                "• Cold Coffee - Rs. 130\n"
                "• Chocolate Brownie - Rs. 120\n\n"
                f"{prompt}"
            }

        # 6. Vegetarian Options
        if any(w in low for w in [
            "vegetarian", "veg option", "veg food", "veg item", "vegetarian option",
            "vegetarian food", "vegetarian item", "only veg", "show veg", "veg"
        ]):
            if self.state != "ordering":
                self.state = "offered_order"
            prompt = "What would you like to add to your order?" if self.state == "ordering" else "Would you like to order any of these?"
            return {
                "message":
                "Here are our vegetarian options:\n\n"
                "Burgers:\n"
                "• Veg Burger - Rs. 140\n"
                "• Cheese Burger - Rs. 160\n\n"
                "Pizza:\n"
                "• Margherita Pizza - Rs. 220\n"
                "• Farmhouse Pizza - Rs. 280\n\n"
                "Pasta:\n"
                "• White Sauce Pasta - Rs. 240\n"
                "• Arrabbiata Pasta - Rs. 230\n\n"
                "Desserts:\n"
                "• Chocolate Brownie - Rs. 120\n"
                "• Ice Cream Sundae - Rs. 150\n\n"
                "Drinks:\n"
                "• Cold Coffee - Rs. 130\n"
                "• Fresh Lime Soda - Rs. 90\n"
                "• Chocolate Shake - Rs. 160\n\n"
                f"{prompt}"
            }

        # 7. Full Menu Query
        if any(w in low for w in [
            "menu", "what do you have", "what food", "show food", "show me food",
            "see the menu", "on the menu", "what can i eat", "full menu", "what's on the menu",
            "whats on the menu", "show menu"
        ]):
            if self.state != "ordering":
                self.state = "offered_order"
            prompt = "What would you like to add to your order?" if self.state == "ordering" else "Would you like to order something?"
            return {
                "message": self.menu_text() + f"\n\n{prompt}"
            }

        # 8. Category Browsing
        for category in self.menu:
            cat_low = category.lower()
            cat_sing = cat_low[:-1] if cat_low.endswith("s") else cat_low
            if cat_low in low or cat_sing in low:
                foods = self.menu[category]
                lines = [f"{category}", ""]
                for name, data in foods.items():
                    lines.append(f"• {name} - Rs. {data['price']}\n  {data['description']}")

                if self.state != "ordering":
                    self.state = "offered_order"
                prompt = "What would you like to add?" if self.state == "ordering" else "Would you like to order one?"
                lines.append(f"\n{prompt}")
                return {"message": "\n\n".join(lines)}

        # 9. Specific Item Search (Price / Information)
        item = self.find_item(low)

        if item and any(word in low for word in [
            "price", "cost", "how much", "tell me", "describe", "what is",
            "about", "information", "rate"
        ]):
            self.pending_item = item[0]
            self.state = "item_confirmation"
            return {"message": f"{item[0]} — Rs. {item[1]['price']}\n{item[1]['description']}\n\nWould you like to order this?"}

        # 10. General Prices Query (no specific item)
        if any(w in low for w in [
            "price", "prices", "cost", "how much is the food", "food cost",
            "how much does your food cost", "show me prices", "what is the price"
        ]):
            lines = ["Here are our current prices:", ""]
            for category, foods in self.menu.items():
                for name, data in foods.items():
                    lines.append(f"• {name} - Rs. {data['price']}")
            if self.state != "ordering":
                self.state = "offered_order"
            prompt = "What would you like to add to your order?" if self.state == "ordering" else "Would you like to order something?"
            lines.append(f"\n{prompt}")
            return {"message": "\n".join(lines)}

        # 11. Item Selection / Order Intent (when item name is matched)
        if item:
            self.pending_item = item[0]
            self.state = "quantity" if self.state == "ordering" else "item_confirmation"
            if self.state == "quantity":
                return {"message": f"{item[0]} — Rs. {self.get_price(item[0])}.\n\nHow many would you like?"}
            return {"message": f"{item[0]} — Rs. {self.get_price(item[0])}.\n\nWould you like to order this?"}

        # 12. General Order Intent
        if any(x in low for x in [
            "order", "buy", "want", "get me", "i'll have", "i will have",
            "give me", "i need", "can i order"
        ]):
            self.state = "ordering"
            return {
                "message":
                "Sure! What would you like to order?\n\nFor example:\n• Chicken Burger\n• Cold Coffee\n• Margherita Pizza"
            }

        if any(x in low for x in ["thanks", "thank you", "thank"]):
            return {"message": "You're very welcome!"}

        return {
            "message":
            "I'm not quite sure what you mean.\n\nYou can try:\n"
            "• Show me the menu\n"
            "• What pizzas do you have?\n"
            "• How much is Cold Coffee?\n"
            "• What are your opening hours?\n"
            "• I want to order\n"
            "• Checkout"
        }