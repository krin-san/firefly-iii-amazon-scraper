from typing import List

from amazon_scraper.amazon.models import *
from amazon_scraper.firefly.models import *


def format_tx_group(group: TransactionGroup):
    return "> " + "\n  - ".join(str(group).split(sep="\n"))

def format_tx_groups(groups: List[TransactionGroup]):
    return "\n".join([format_tx_group(item) for item in groups])

def format_tx_urls(groups: List[TransactionGroup], host: str):
    return "\n".join([f"  - {host}/transactions/show/{item.id}" for item in groups])
