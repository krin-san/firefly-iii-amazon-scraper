from typing import List

from amazon_scraper.amazon.models import *
from amazon_scraper.firefly.models import *


def log_separator():
    return "----------------------------------------------------------------\n"

def log_tx_group(transaction: TransactionGroup):
    return "> " + "\n  - ".join(str(transaction).split(sep="\n"))

def log_tx_groups(transactions: List[TransactionGroup]):
    return "\n".join([log_tx_group(item) for item in transactions])
