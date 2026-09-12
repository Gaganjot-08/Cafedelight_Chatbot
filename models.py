from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class PlacedOrder(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    order_type = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(300), nullable=True)
    items_json = db.Column(db.Text, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def items(self):
        return json.loads(self.items_json)