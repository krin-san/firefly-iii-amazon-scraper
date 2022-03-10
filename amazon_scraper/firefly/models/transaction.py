from typing import List, Union

from amazon_scraper.firefly.models.tags import Tags


class Transaction:
    def __init__(self, id: int, description: str, amount: str, currency_code: str = "EUR", notes: Union[str, None] = None, tags: Union[List[str], None] = None, internal_reference: Union[str, None] = None, external_url: Union[str, None] = None, json: Union[dict, None] = None):
        self._id = id
        self.description = description
        self.amount = amount
        self.currency_code = currency_code
        self.notes = notes
        self.tags = tags if tags is not None else []
        self.internal_reference = internal_reference
        self.external_url = external_url
        self.json = json if json is not None else {}

    @staticmethod
    def from_json(json: dict):
        return Transaction(
            id=int(json["transaction_journal_id"]),
            description=json["description"],
            amount=json["amount"],
            currency_code=json["currency_code"],
            notes=json["notes"],
            tags=json["tags"],
            internal_reference=json["internal_reference"],
            external_url=json["external_url"],
            json=Transaction.minify_json(json)
        )

    @staticmethod
    def minify_json(json: dict):
        """Modify json to prepare it for update operations"""

        # Remove keys which are not allowed to be sent
        json = include_keys(json, [
            "amount", "book_date", "budget_id", "category_name", "currency_id", "date", "description",
            "destination_id", "destination_name", "due_date", "external_url", "foreign_amount",
            "foreign_currency_id", "interest_date", "internal_reference", "invoice_date", "notes",
            "payment_date", "process_date", "source_id", "source_name", "tags", "transaction_journal_id", "type",
        ])
        # Transform fields which couldn't be sent as is
        foreign_currency_id = int(json["foreign_currency_id"]) if "foreign_currency_id" in json and json["foreign_currency_id"] is not None else None
        json["foreign_currency_id"] = foreign_currency_id if foreign_currency_id != 0 else None

        return json

    @property
    def id(self):
        return self._id

    def __eq__(self, other): 
        if not isinstance(other, Transaction):
            return False
        return self.id == other.id and self.description == other.description and self.amount == other.amount and self.currency_code == other.currency_code and self.notes == other.notes and self.tags == other.tags and self.internal_reference == other.internal_reference and self.external_url == other.external_url

    def __str__(self):
        return f'jid: {self._id}, amount: {self.currency_code} {float(self.amount):.2f}, description: {self.description}, tags: {self.tags}, url: {self.external_url}, iref: {self.internal_reference}, notes: {self.notes}'

    def copy(self):
        return Transaction.from_json({
            **self.to_json(),
            "transaction_journal_id": 0, # New transaction
            "currency_code": self.currency_code, # Excluded from json
            "amount": "0.01", # Should be > 0
        })

    def to_json(self):
        return exclude_keys({
            **self.json,
            "description": self.description,
            "amount": self.amount,
            "notes": self.notes,
            "tags": self.tags,
            "external_url": self.external_url,
            "internal_reference": self.internal_reference,
        }, ["currency_code"])

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

def exclude_keys(dictionary: dict, keys: list):
    """Filters a dict by excluding certain keys."""
    key_set = set(dictionary.keys()) - set(keys)
    return {key: dictionary[key] for key in key_set}
