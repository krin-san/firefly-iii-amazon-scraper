import logging
import unittest
from difflib import ndiff
from typing import List, Union
from unittest.mock import Mock
from xml.dom import NotFoundErr

from amazon_scraper.actions import fetch as action
from amazon_scraper.actions.common import format_list
from amazon_scraper.amazon.models.order import AmazonOrder
from amazon_scraper.amazon.models.shipment import AmazonShipment
from amazon_scraper.amazon.models.shipment_item import AmazonShipmentItem
from amazon_scraper.amazon.scraper import AmazonScraper
from amazon_scraper.deps import AppArgs, Runner
from amazon_scraper.firefly.api import FireflyAPI
from amazon_scraper.firefly.models.tags import Tags
from amazon_scraper.firefly.models.transaction import Transaction
from amazon_scraper.firefly.models.transaction_group import TransactionGroup

ANY_VALUE="TEST_ANY_VALUE"

class TestActionsFetch(unittest.TestCase):
    amazon: Mock
    firefly: Mock
    args: Mock

    def update_transaction(self) -> Mock:
        return self.firefly.update_transaction

    # Helpers

    def process_and_compare(self, given: List[TransactionGroup], expected: List[TransactionGroup]):
        action.process_order("123", given, Runner(self.amazon, self.firefly, self.args))
        result: List[TransactionGroup] = [x.args[0] for x in self.update_transaction().call_args_list]
        self.replace_any_values(result, expected)
        self.assertEqual(result, expected, "Lists differ (result vs expected):\n\n" + "".join(ndiff(format_list(result).splitlines(keepends=True), format_list(expected).splitlines(keepends=True))))

    def replace_any_values(self, result: List[TransactionGroup], expected: List[TransactionGroup]):
        for gi, group in enumerate(expected):
            for ti, tx in enumerate(group.transactions):
                if tx.notes == ANY_VALUE:
                    tx.notes = result[gi].transactions[ti].notes

    def what_is_wrong(self, expected: List[TransactionGroup]):
        print(f"\nGiven:\n{format_list([x.args[0] for x in self.update_transaction().call_args_list])}\n\nExpected:\n{format_list(expected)}\n")

    # Tests

    def setUp(self):
        logging.getLogger().setLevel(logging.CRITICAL)
        self.maxDiff = None
        self.longMessage = False

        self.amazon = Mock(AmazonScraper)
        self.firefly = Mock(FireflyAPI)
        self.args = Mock(AppArgs)

        self.amazon.host = "AMAZON"
        self.firefly.host = "FIREFLY"
        self.args.dry_run = False

    def test_1by1_error(self):
        self.amazon.scrape_order.side_effect = NotFoundErr()
        given = [
            TransactionGroup("1", None, [
                Transaction(1, "123 noise ABC", "4.00"),
            ]),
        ]
        expected = []
        self.process_and_compare(given, expected)

    def test_1by1_match_equalPrice(self):
        self.amazon.scrape_order.return_value = order_with([
            [
                AmazonShipmentItem("AMAZON/item/20", "Socks", "EUR", "2.50", 2),
            ],
        ])
        given = [
            TransactionGroup("1", None, [
                Transaction(1, "123 noise ABC", "5.00"),
            ]),
        ]
        expected = [
            TransactionGroup("1", None, [
                Transaction(
                    1, "123 noise ABC", "5.00",
                    tags=[Tags.MATCH],
                    notes="Socks",
                    internal_reference="EUR 2.50 x2 @ AMAZON/item/20",
                    external_url="AMAZON/order/123",
                ),
            ]),
        ]
        self.process_and_compare(given, expected)

    def test_1by1_match_promoPrice(self):
        self.amazon.scrape_order.return_value = order_with([
            [
                AmazonShipmentItem("AMAZON/item/20", "Socks", "EUR", "2.50", 2),
            ],
        ], promotion=1.0)
        given = [
            TransactionGroup("1", None, [
                Transaction(1, "123 noise ABC", "4.00"),
            ]),
        ]
        expected = [
            TransactionGroup("1", None, [
                Transaction(
                    1, "123 noise ABC", "4.00",
                    tags=[Tags.MATCH],
                    notes="Socks",
                    internal_reference="EUR 2.50 x2 @ AMAZON/item/20",
                    external_url="AMAZON/order/123",
                ),
            ]),
        ]
        self.process_and_compare(given, expected)

    def test_1by1_manual(self):
        self.amazon.scrape_order.return_value = order_with([
            [
                AmazonShipmentItem("AMAZON/item/20", "Socks", "EUR", "2.50", 2),
                AmazonShipmentItem("AMAZON/item/21", "Tie", "EUR", "5.00", 1),
            ],
        ])
        given = [
            TransactionGroup("1", None, [
                Transaction(1, "123 noise ABC", "11.00"), # 2.5*2+5 = 10 != 11
            ]),
        ]
        expected = [
            TransactionGroup("1", "123 noise ABC", [
                Transaction(
                    1, "123 noise ABC", "11.00",
                    tags=[Tags.LAST, Tags.TODO],
                    notes="Socks",
                    internal_reference="EUR 2.50 x2 @ AMAZON/item/20",
                    external_url="AMAZON/order/123",
                ),
                Transaction(
                    0, "123 noise ABC", "0.01",
                    tags=[Tags.LAST, Tags.TODO],
                    notes="Tie",
                    internal_reference="EUR 5.00 @ AMAZON/item/21",
                    external_url="AMAZON/order/123",
                ),
            ]),
        ]
        self.process_and_compare(given, expected)

    def test_1by1_lastMatch_differentPrice(self):
        self.amazon.scrape_order.return_value = order_with([
            [
                AmazonShipmentItem("AMAZON/item/20", "Socks", "EUR", "2.50", 2),
            ],
        ])
        given = [
            TransactionGroup("1", None, [
                Transaction(1, "123 noise ABC", "6.00"), # +1 EUR delivery
            ]),
        ]
        expected = [
            TransactionGroup("1", None, [
                Transaction(
                    1, "123 noise ABC", "6.00",
                    tags=[Tags.LAST],
                    notes="Socks",
                    internal_reference="EUR 2.50 x2 @ AMAZON/item/20",
                    external_url="AMAZON/order/123",
                ),
            ]),
        ]
        self.process_and_compare(given, expected)

    def test_2by2_match_equalPrice(self):
        self.amazon.scrape_order.return_value = order_with([
            [
                AmazonShipmentItem("AMAZON/item/10", "Coffee", "EUR", "10.00", 1),
                AmazonShipmentItem("AMAZON/item/11", "Tea", "EUR", "5.00", 2),
            ], [
                AmazonShipmentItem("AMAZON/item/20", "Socks", "EUR", "2.50", 2),
                AmazonShipmentItem("AMAZON/item/21", "Tie", "EUR", "5.00", 1),
            ]
        ])
        given = [
            TransactionGroup("1", None, [
                Transaction(1, "123 noise ABC", "20.00"),
            ]),
            TransactionGroup("2", None, [
                Transaction(2, "123 noise DEF", "10.00"),
            ]),
        ]
        expected = [
            TransactionGroup("1", "123 noise ABC", [
                Transaction(
                    1, "123 noise ABC", "10.00",
                    tags=[Tags.MATCH],
                    notes="Coffee",
                    internal_reference="EUR 10.00 @ AMAZON/item/10",
                    external_url="AMAZON/order/123",
                ),
                Transaction(
                    0, "123 noise ABC", "10.00",
                    tags=[Tags.MATCH],
                    notes="Tea",
                    internal_reference="EUR 5.00 x2 @ AMAZON/item/11",
                    external_url="AMAZON/order/123",
                ),
            ]),
            TransactionGroup("2", "123 noise DEF", [
                Transaction(
                    2, "123 noise DEF", "5.00",
                    tags=[Tags.MATCH],
                    notes="Socks",
                    internal_reference="EUR 2.50 x2 @ AMAZON/item/20",
                    external_url="AMAZON/order/123",
                ),
                Transaction(
                    0, "123 noise DEF", "5.00",
                    tags=[Tags.MATCH],
                    notes="Tie",
                    internal_reference="EUR 5.00 @ AMAZON/item/21",
                    external_url="AMAZON/order/123",
                ),
            ]),
        ]
        self.process_and_compare(given, expected)

    def test_2by2_manual(self):
        self.amazon.scrape_order.return_value = order_with([
            [
                AmazonShipmentItem("AMAZON/item/10", "Coffee", "EUR", "10.00", 1),
                AmazonShipmentItem("AMAZON/item/11", "Tea", "EUR", "5.00", 2),
            ], [
                AmazonShipmentItem("AMAZON/item/20", "Socks", "EUR", "2.50", 2),
                AmazonShipmentItem("AMAZON/item/21", "Tie", "EUR", "5.00", 1),
            ]
        ])
        given = [
            TransactionGroup("1", None, [
                Transaction(1, "123 noise ABC", "21.00"),
            ]),
            TransactionGroup("2", None, [
                Transaction(2, "123 noise DEF", "11.00"),
            ]),
        ]
        expected = [
            TransactionGroup("1", None, [
                Transaction(
                    1, "123 noise ABC", "21.00",
                    tags=[Tags.MANUAL, Tags.TODO],
                    notes=ANY_VALUE,
                    external_url="AMAZON/order/123",
                ),
            ]),
            TransactionGroup("2", None, [
                Transaction(
                    2, "123 noise DEF", "11.00",
                    tags=[Tags.MANUAL, Tags.TODO],
                    notes=ANY_VALUE,
                    external_url="AMAZON/order/123",
                ),
            ]),
        ]
        self.process_and_compare(given, expected)

def order_with(items: list, promotion: Union[float, None] = None):
    if len(items) == 0 or isinstance(items[0], AmazonShipmentItem):
        shipments = [AmazonShipment(1, items)]
    elif isinstance(items[0], list):
        shipments = [AmazonShipment(index, items) for index, items in enumerate(items)]
    else:
        raise TypeError(f"Expected List[AmazonShipmentItem] or List[List[AmazonShipmentItem]], got {type(items)}")

    summary = f"Promotion Applied: -EUR {promotion:.2f}" if promotion is not None else ""
    return AmazonOrder("AMAZON/order/123", summary, "", shipments)

if __name__ == '__main__':
    unittest.main()
