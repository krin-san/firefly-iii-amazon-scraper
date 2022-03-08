from typing import List

from amazon_scraper.firefly.models.tags import Tags


class Transaction:
    def __init__(self, json: dict):
        self._id: str = json["transaction_journal_id"]
        self.description: str = json["description"]
        self._currency_code: str = "EUR" # FIXME: currency_code is not supposed to be sent in PUT request
        self.amount: str = json["amount"]
        self.notes: str = json["notes"]
        self.tags: List[str] = json["tags"]
        self.internal_reference: str = json["internal_reference"] # Price @ Product URL
        self.external_url: str = json["external_url"] # Order URL
        self.json = include_keys(json, [
            "amount", "book_date", "budget_id", "category_name", "currency_id", "date", "description",
            "destination_id", "destination_name", "due_date", "external_url", "foreign_amount",
            "foreign_currency_id", "interest_date", "internal_reference", "invoice_date", "notes",
            "payment_date", "process_date", "source_id", "source_name", "tags", "transaction_journal_id", "type",
        ])
        # Transform fields which couldn't be sent as is
        foreign_currency_id = int(json["foreign_currency_id"]) if "foreign_currency_id" in json and json["foreign_currency_id"] is not None else None
        self.json["foreign_currency_id"] = foreign_currency_id if foreign_currency_id != 0 else None

    @property
    def id(self):
        return self._id

    def __str__(self):
        return f'jid: {self._id}, amount: {self._currency_code} {float(self.amount):.2f}, description: {self.description}, tags: {self.tags}, url: {self.external_url}, iref: {self.internal_reference}, notes: {self.notes}'

    def copy(self):
        return Transaction({
            **self.to_json(),
            "transaction_journal_id": 0, # New transaction
            "amount": "0.01", # Should be > 0
        })

    def to_json(self):
        return {
            **self.json,
            "description": self.description,
            "amount": self.amount,
            "notes": self.notes,
            "tags": self.tags,
            "external_url": self.external_url,
            "internal_reference": self.internal_reference,
        }

    def remove_tags(self):
        for tag in Tags.all():
            if tag in self.tags:
                self.tags.remove(tag)

    def add_tags(self, tags: List[str]):
        self.tags.extend(tags)

    def set_tags(self, tags: List[str]):
        self.remove_tags()
        self.add_tags(tags)


def include_keys(dictionary: dict, keys: list):
    """Filters a dict by only including certain keys."""
    key_set = set(keys) & set(dictionary.keys())
    return {key: dictionary[key] for key in key_set}
