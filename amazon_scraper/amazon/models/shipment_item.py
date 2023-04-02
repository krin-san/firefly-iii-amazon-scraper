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
        (currency, amount) = ITEM_PRICE_RE.match(price.text.strip()).groups()
        return AmazonShipmentItem(
            host + PRODUCT_HREF_RE.match(link["href"]).group(0),
            link.text.strip(),
            currency,
            amount,
            int(quantity.text.strip()) if quantity is not None else 1,
        )

    @staticmethod
    def from_json(json):
        return AmazonShipmentItem(**json)

    def __str__(self):
        return f"{self.price_note} @ {self.url} | {self.name}"

    @cached_property
    def price_note(self):
        return f'{self.currency} {self.amount}{f" x{self.quantity}" if self.quantity > 1 else ""}'
