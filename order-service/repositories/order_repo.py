from sqlalchemy.orm import Session

from models import Basket, Order


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_from_basket(self, order: Order, basket: Basket) -> Order:
        self.db.add(order)
        self.db.delete(basket)
        self.db.commit()
        return order
