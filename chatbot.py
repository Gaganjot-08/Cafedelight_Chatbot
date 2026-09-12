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

        for key, value in self.all_items().items():
            if key in low:
                return value

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
            f"{name}\n"
            f"Price: Rs. {data['price']}\n"
            f"Category: {category}\n\n"
            f"{data['description']}"
        )

    def is_yes(self, text):
        low = text.lower().strip()
        yes_words = [
            "yes", "y", "yeah", "yep", "yup", "sure", "okay", "ok",
            "of course", "definitely", "please", "i do", "i want it",
            "yes please", "sure thing", "i'll have one", "i want to order it",
            "i want this", "add it"
        ]
        return low in yes_words or any(w in low for w in ["yes please", "i want it", "i'll have one", "order it"])

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
                self.state = None
                self.pending_item = None
                return {
                    "message":
                    "No problem.\n\nWould you like to see something else from the menu?"
                }
            return {
                "message": "Please answer Yes or No.\n\nWould you like to order this item?"
            }

        if self.state == "quantity":
            try:
                match = re.search(r"\d+", low)
                if not match:
                    words_num = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
                    qty = 0
                    for w, val in words_num.items():
                        if w in low:
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
            self.state = None
            self.pending_item = None

            return {
                "action": "add_item",
                "item": item,
                "quantity": qty,
                "message":
                f"Added {qty} x {item} to your cart.\n\nWould you like anything else?"
            }

        if self.state == "name":
            if len(text.strip()) < 2:
                return {"message": "Please enter your name."}

            customer["name"] = text.strip()
            self.state = "phone"

            return {
                "action": "set_customer",
                "field": "name",
                "value": text.strip(),
                "message":
                f"Nice to meet you, {text.strip()}!\n\nNow please provide your phone number."
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
                return {
                    "message": "Please choose one:\n\nDine-in\nTakeaway\nDelivery"
                }

            customer["order_type"] = value

            if value == "Delivery":
                self.state = "address"
                return {
                    "action": "set_customer",
                    "field": "order_type",
                    "value": value,
                    "message":
                    "Delivery selected.\n\nPlease enter your complete delivery address."
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
                "message":
                "Delivery address saved successfully.\n\nSay 'checkout' when you are ready to place the order."
            }

        if self.is_done_with_order(low):
            if current_order:
                return {"action": "checkout", "message": ""}
            return {"message": "Your cart is currently empty."}

        # 1. Opening Hours Intent
        if any(w in low for w in [
            "opening hour", "opening hours", "business hour", "business hours",
            "restaurant hour", "restaurant hours", "what time do you open",
            "what time do you close", "when do you open", "when do you close",
            "when are you open", "are you open", "open today", "operating hours"
        ]):
            return {
                "message":
                "Cafe Delight Opening Hours:\n\n"
                "• Monday – Sunday: 10:00 AM – 10:00 PM\n\n"
                "Would you like to order something?"
            }

        # 2. Greetings
        if any(x in low for x in ["hello", "hi", "hey", "namaste"]):
            return {
                "message":
                "Hello!\n\nWelcome to Cafe Delight.\nWould you like to see our menu or place an order?"
            }

        # 3. Popular Items / Recommendations
        if any(w in low for w in [
            "popular", "best seller", "bestseller", "recommend", "special",
            "today's special", "todays special", "top item", "favorite", "favourite"
        ]):
            return {
                "message":
                "Here are our most popular customer favorites:\n\n"
                "• Chicken Burger - Rs. 180\n"
                "• Margherita Pizza - Rs. 220\n"
                "• Cold Coffee - Rs. 130\n"
                "• Chocolate Brownie - Rs. 120\n\n"
                "Would you like to order one of these?"
            }

        # 4. Vegetarian Options
        if any(w in low for w in [
            "vegetarian", "veg option", "veg food", "veg item", "vegetarian option",
            "vegetarian food", "vegetarian item", "only veg", "show veg"
        ]):
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
                "Would you like to order any of these?"
            }

        # 5. Full Menu Query
        if any(w in low for w in [
            "menu", "what do you have", "what food", "show food", "show me food",
            "see the menu", "on the menu", "what can i eat", "full menu"
        ]):
            return {
                "message": self.menu_text() + "\n\nWould you like to order something?"
            }

        # 6. Category Browsing
        for category in self.menu:
            if category.lower() in low:
                foods = self.menu[category]
                lines = [f"{category}", ""]
                for name, data in foods.items():
                    lines.append(f"• {name} - Rs. {data['price']}\n  {data['description']}")
                lines.append("\nWould you like to order one?")
                return {"message": "\n\n".join(lines)}

        # 7. Checkout Trigger
        if any(x in low for x in [
            "checkout", "place order", "confirm order", "finish order",
            "complete order", "order now"
        ]):
            return {"action": "checkout", "message": ""}

        # 8. Specific Item Search (Price / Information)
        item = self.find_item(low)

        if item and any(word in low for word in [
            "price", "cost", "how much", "tell me", "describe", "what is",
            "about", "information", "rate"
        ]):
            self.pending_item = item[0]
            self.state = "item_confirmation"
            return {"message": self.item_info(item) + "\n\nWould you like to order it?"}

        # 9. General Prices Query (no specific item)
        if any(w in low for w in ["price", "prices", "cost", "how much is the food", "food cost"]):
            lines = ["Here are our current prices:", ""]
            for category, foods in self.menu.items():
                for name, data in foods.items():
                    lines.append(f"• {name} - Rs. {data['price']}")
            lines.append("\nWould you like to order something?")
            return {"message": "\n".join(lines)}

        # 10. Item Selection / Order Intent
        if item:
            self.pending_item = item[0]
            self.state = "item_confirmation"
            return {"message": self.item_info(item) + "\n\nWould you like to order it?"}

        if any(x in low for x in [
            "order", "buy", "want", "get me", "i'll have", "i will have",
            "give me", "i need", "can i order"
        ]):
            return {
                "message":
                "Sure!\n\nWhat would you like to order?\n\nFor example:\nChicken Burger\nCold Coffee\nMargherita Pizza"
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