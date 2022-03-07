from amazon_scraper.firefly.models.common import *


class AmazonInfo:
    def __init__(self, order_id: str, tx_id: str):
        self.original_id = order_id
        self.order_id = order_id.replace(".", "-")
        self.tx_id = tx_id

    @staticmethod
    def parse_titles(titles: list):
        for title in titles:
            if title is not None and (match := AMZN_TX_RE.match(title)) is not None:
                return AmazonInfo(*match.groups())
