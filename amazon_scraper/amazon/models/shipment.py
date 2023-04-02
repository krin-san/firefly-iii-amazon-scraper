from functools import cached_property
from typing import List

from amazon_scraper.amazon.models.common import *
from amazon_scraper.amazon.models.shipment_item import AmazonShipmentItem
from bs4.element import Tag


class AmazonShipment:
    def __init__(self, title: str, items: List[AmazonShipmentItem]):
        self.title = title
        self.items = items

    @staticmethod
    def from_details(shipment: Tag, host: str):
        title = shipment.select_one("div.shipment-top-row div.a-row")
        # div.a-box-inner div.a-fixed-right-grid.a-spacing-top-medium div.a-fixed-right-grid-inner.a-grid-vertical-align.a-grid-top div.a-fixed-right-grid-col.a-col-left div.a-row
        row = shipment.select_one("div.a-col-left div.a-row")
        # div.a-fixed-left-grid.a-spacing-base div.a-fixed-left-grid-inner div.a-fixed-left-grid-col.a-col-right div.a-row a.a-link-normal
        links = list(filter(
            lambda x: PRODUCT_HREF_RE.match(x["href"]) is not None,
            row.select("div.a-col-right div.a-row a.a-link-normal")
        ))
        # div.a-fixed-left-grid.a-spacing-base div.a-fixed-left-grid-inner div.a-fixed-left-grid-col.a-col-right div.a-row span.a-size-small.a-color-price nobr
        prices = row.select("div.a-col-right div.a-row span.a-color-price nobr")
        # div.a-fixed-left-grid.a-spacing-none div.a-fixed-left-grid-inner div.a-text-center.a-fixed-left-grid-col.a-col-left div.item-view-left-col-inner span.item-view-qty
        quantities = [item.select_one("span.item-view-qty") for item in row.select("div.a-col-left")]
        assert len(links) > 0, "No shipment items were found"
        assert len(links) == len(prices) == len(quantities), f"Counts should match: {len(links)} links, {len(prices)} prices, {len(quantities)} quantities"
        return AmazonShipment(
            title.text.strip(),
            list(map(lambda x: AmazonShipmentItem.from_details(*x, host), zip(links, prices, quantities))),
        )

    @staticmethod
    def from_json(json):
        return AmazonShipment(**{
            **json,
            "items": [AmazonShipmentItem.from_json(item) for item in json["items"]]
        })

    def __str__(self):
        return f"{self.title} | {self.currency} {self.amount}" + "\n- " + "\n- ".join([str(item) for item in self.items])

    @cached_property
    def currency(self):
        return self.items[0].currency

    @cached_property
    def amount(self):
        return f'{sum([float(item.amount) * float(item.quantity) for item in self.items]):.2f}'

    @cached_property
    def is_refund(self):
        return REFUND_RE.match(self.title) is not None
