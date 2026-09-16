# Cafe Delight — Café Ordering Chatbot

Cafe Delight is a web-based café ordering system built with Python and Flask. It allows customers to interact with a chatbot to browse the café menu, ask about food and prices, add items to a cart, provide their order details, and place an order.

After an order is confirmed, it is saved in a SQLite database and an email notification is sent to the café.

## What the Program Does

The customer can:

* View the café menu and food categories
* Ask for item prices and descriptions
* View popular and vegetarian options
* Order one or more food items
* Specify quantities
* View, remove, or clear cart items
* Choose Dine-in, Takeaway, or Delivery
* Provide their name and phone number
* Provide a delivery address when required
* Review the order before confirming
* Confirm or cancel the order

Once confirmed, the application generates an order number, stores the order, and sends the order information to the café by email.

## How It Works

The application follows a simple flow:

```text
Customer
   ↓
Chatbot
   ↓
Menu & Order Selection
   ↓
Cart
   ↓
Checkout
   ↓
Order Confirmation
   ↓
SQLite Database
   ↓
Email Notification
```

The chatbot is rule-based. It processes the customer's message using keywords, menu-item matching, quantity detection, and conversation states. This allows it to handle a multi-step conversation such as asking for an item, quantity, customer information, and final confirmation.

## Technology Stack

| Technology          | Purpose                    |
| ------------------- | -------------------------- |
| Python              | Main programming language  |
| Flask               | Web application and API    |
| Flask-SQLAlchemy    | Database integration       |
| SQLite              | Stores completed orders    |
| HTML/CSS/JavaScript | Web interface              |
| SMTP/Gmail          | Order email notifications  |
| Python `re`         | Message and input matching |
| Python `json`       | Order data storage         |

The project uses Flask 3.0.3 and Flask-SQLAlchemy 3.1.1.

## Project Structure

```text
Cafe-Delight/
│
├── app.py
├── chatbot.py
├── menu.py
├── models.py
├── email_service.py
├── email_config.py
├── requirements.txt
│
├── templates/
│   └── index.html
│
└── static/
```

### Main Files

**`app.py`** — Main Flask application. Connects the chatbot, cart, checkout, database, and email system.

**`chatbot.py`** — Contains the chatbot logic, including message understanding, menu-item matching, quantities, and conversation states.

**`menu.py`** — Contains the café menu, including categories, prices, and descriptions.

**`models.py`** — Defines the database structure used to store completed orders.

**`email_service.py`** — Creates and sends order notification emails to the café.

**`email_config.py`** — Contains the email and SMTP configuration.

**`requirements.txt`** — Lists the Python dependencies required by the project.

## Menu

The current menu contains five categories:

* Burgers
* Pizza
* Pasta
* Drinks
* Desserts

Each item has a price and description stored in `menu.py`.

## Order Process

A typical order works like this:

```text
1. Customer selects food
2. Items are added to the cart
3. Customer starts checkout
4. Name and phone number are collected
5. Order type is selected
6. Delivery address is collected if needed
7. Final order summary is shown
8. Customer confirms the order
9. Order is saved to SQLite
10. Café receives an email notification
```

## Database

Completed orders are stored in a SQLite database:

```text
cafe.db
```

Each order stores information such as the order number, customer details, order type, items, total price, email status, and creation time.

## Email Notifications

The application uses Gmail SMTP to notify the café when an order is confirmed.

The email contains the customer information, order details, quantities, prices, total amount, and order time.

A Gmail account with 2-Step Verification and a Google App Password is required for email sending.

**Important:** Never commit real email passwords or App Passwords to GitHub. Store them securely using environment variables or another secret-management method.

## Installation

Clone the repository:

```bash
git clone https://github.com/Gaganjot-08/Cafedelight_Chatbot.git
cd Cafe-Delight
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

## Run the Application

Start the Flask application:

```bash
python app.py
```

Then open:

```text
http://127.0.0.1:5000
```

## Example

```text
Customer: I want 2 Chicken Burgers

Bot: Added 2 x Chicken Burger to your cart.

Customer: Checkout

Bot: [Collects customer details]

Customer: Confirm

Bot: ORDER CONFIRMED!
```

The order is then stored in the database and the café is notified by email.

## Project Overview

Cafe Delight combines a rule-based conversational interface with a traditional ordering system. The chatbot handles the conversation, Flask manages the web application and requests, SQLite stores completed orders, and Gmail SMTP handles café notifications.

It is designed as a simple foundation that can later be extended with features such as online payments, customer accounts, order tracking, an admin dashboard, and more advanced natural-language understanding.
