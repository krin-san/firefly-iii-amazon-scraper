import json
from functools import cached_property
from typing import List

from amazon_scraper.amazon.models.common import *
from amazon_scraper.amazon.models.shipment import AmazonShipment
from bs4.element import Tag


class AmazonOrder:
    def __init__(self, url: str, summary: str, transactions: str, shipments: List[AmazonShipment]):
        assert len(shipments) > 0, "Order cannot exist without shipments"
        self.url = url
        self.summary = summary
        self.transactions = transactions
        self.shipments = shipments

    @staticmethod
    def from_details(details: Tag, url: str, host: str):
        return AmazonOrder(
            url,
            # div#a-page div#orderDetails div.a-box-group.a-spacing-base div.a-box.a-first div.a-box-inner div.a-fixed-right-grid div.a-fixed-right-grid-inner div#od-subtotals.a-fixed-right-grid-col.a-col-right
            AmazonOrder._parse_summary(details.select_one("div#od-subtotals")),
            # div#a-page div#orderDetails div.a-box-group.a-spacing-base div.a-box.a-last div.a-box-inner div.a-row.a-expander-container.a-expander-inline-container.show-if-no-js
            AmazonOrder._parse_transactions(details.select_one("div.a-box-group div.a-box.a-last div.a-row")),
            # div#a-page div#orderDetails [div.a-box-group.od-shipments]? div.a-box.shipment.shipment-is-delivered
            list(map(lambda x: AmazonShipment.from_details(*x, host), enumerate(details.select("div.shipment")))),
        )

    @staticmethod
    def _parse_summary(summary: Tag):
        return "\n".join(list(filter(lambda x: x, [
            " ".join([
                cell.text.strip() for cell in row.select("div.a-column span")
            ]) for row in summary.select("div.a-row")
        ])))

    @staticmethod
    def _parse_transactions(transactions: Tag):
        return "\n".join([
            re.sub(r"\s+", " ", row.text.strip()) for row in transactions.select("div.a-row")
        ])

    @staticmethod
    def from_json(json):
        return AmazonOrder(**{
            **json,
            "shipments": [AmazonShipment.from_json(item) for item in json["shipments"]]
        })

    def __str__(self):
        return "{}\nSummary:\n{}\nTransactions:\n{}\nShipments:\n{}".format(
            self.url,
            "\n".join(["  " + line for line in self.summary.splitlines()]),
            "\n".join(["  " + line for line in self.transactions.splitlines()]),
            "\n".join(["  " + line for item in self.shipments for line in str(item).splitlines()])
        )

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    @cached_property
    def promotion(self):
        matches = SUMMARY_PROMO_RE.findall(self.summary)
        return float(matches[0].replace(",", ".")) if len(matches) > 0 else 0.0
