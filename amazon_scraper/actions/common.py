from typing import List

from amazon_scraper.amazon.models import *
from amazon_scraper.firefly.models import *


def format_tx_group(group: TransactionGroup):
    return "> " + "\n  - ".join(str(group).split(sep="\n"))

def format_tx_groups(groups: List[TransactionGroup]):
    return "\n".join([format_tx_group(item) for item in groups])

def format_tx_urls(groups: List[TransactionGroup], host: str):
    return "\n".join([f"  - {host}/transactions/show/{item.id}" for item in groups])

def match_tx(tx: Transaction, item: AmazonShipmentItem, order_url: str, set_amount: bool):
    if set_amount:
        tx.amount = f'{float(item.amount) * float(item.quantity):.2f}'

    tx.external_url = order_url
    tx.internal_reference = f"{item.price_note} @ {item.url}"
    tx.notes = item.name
