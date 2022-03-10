from functools import cached_property
from typing import List, Union

from amazon_scraper.firefly.models.amazon_info import AmazonInfo
from amazon_scraper.firefly.models.transaction import Transaction


class TransactionGroup:
    def __init__(self, id: str, group_title: Union[str, None], transactions: List[Transaction]):
        self._id = id
        self.group_title = group_title
        self.transactions = transactions

    @staticmethod
    def from_json(json: dict):
        attributes = json["attributes"]
        group_title = attributes["group_title"]
        transactions = [Transaction.from_json(json) for json in attributes["transactions"]]
        transactions.sort(key=lambda x: int(x.id)) # lesser IDs go first
        return TransactionGroup(
            id=json["id"],
            group_title=group_title,
            transactions=transactions,
        )

    @property
    def id(self):
        return self._id

    @cached_property
    def amazon_info(self):
        return AmazonInfo.parse_titles([self.group_title, *[tx.description for tx in self.transactions]])

    @cached_property
    def amount(self):
        return f'{sum([float(item.amount.replace(",", ".")) for item in self.transactions]):.2f}'

    def __eq__(self, other): 
        if not isinstance(other, TransactionGroup):
            return False
        return self.id == other.id and self.group_title == other.group_title and self.transactions == other.transactions

    def __str__(self):
        return f'id: {self.id}, group_title: {self.group_title}, transactions:' + "\n- " + "\n- ".join([str(item) for item in self.transactions])

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
