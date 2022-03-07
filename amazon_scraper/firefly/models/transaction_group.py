from functools import cached_property
from typing import List

from amazon_scraper.firefly.models.amazon_info import AmazonInfo
from amazon_scraper.firefly.models.transaction import Transaction


class TransactionGroup:
    def __init__(self, json):
        self._id: str = json["id"]
        attributes = json["attributes"]
        self.group_title: str = attributes["group_title"]
        self.transactions = [Transaction(json) for json in attributes["transactions"]]
        self.transactions.sort(key=lambda x: int(x.id)) # lesser IDs go first
        self.amazon_info = AmazonInfo.parse_titles([self.group_title, *[tx.description for tx in self.transactions]])

    @property
    def id(self):
        return self._id

    @cached_property
    def amount(self):
        return f'{sum([float(item.amount.replace(",", ".")) for item in self.transactions]):.2f}'

    def __str__(self):
        return f'id: {self.id}, group_title: {self.group_title}, transactions:\n' + "\n".join([str(item) for item in self.transactions])

    def to_json(self):
        return {
            **({"group_title": self.group_title} if self.group_title is not None else {}),
            "transactions": [tx.to_json() for tx in self.transactions]
        }

    def add_tags(self, tags: List[str]):
        for tx in self.transactions:
            tx.add_tags(tags)

    def set_tags(self, tags: List[str]):
        for tx in self.transactions:
            tx.set_tags(tags)
