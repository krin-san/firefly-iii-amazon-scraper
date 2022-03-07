from functools import cached_property

from amazon_scraper.amazon.models.common import *
from bs4.element import Tag


class AmazonShipmentItem:
    def __init__(self, url: str, name: str, currency: str, amount: str, quantity: int):
        self.url = url
        self.name = name
        self.currency = currency
        self.amount = amount.replace(",", ".")
        self.quantity = quantity

    @staticmethod
    def from_details(link: Tag, price: Tag, quantity: Tag, host: str):
        return AmazonShipmentItem(
            host + PRODUCT_HREF_RE.match(link["href"]).group(0),
            link.text.strip(),
            *price.text.split(),
            int(quantity.text.strip()) if quantity is not None else 1,
        )

    @staticmethod
    def from_json(json):
        return AmazonShipmentItem(**json)

    @cached_property
    def price_note(self):
        return f'{self.currency} {self.amount}{f" x{self.quantity}" if self.quantity > 1 else ""}'

    def notes(self):
        return "\n".join([
            f"- {self.price_note} {self.url}   ",
            f"  {self.name}",
        ])
