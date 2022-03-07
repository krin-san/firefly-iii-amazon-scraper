"""Fetches Amazon order info for new transaction groups which don't have notes attached."""

import traceback
from itertools import groupby
from typing import List

from amazon_scraper.actions.common import *
from amazon_scraper.deps import Runner
from amazon_scraper.firefly.models import *


def run(runner: Runner):
    groups = [TransactionGroup(json) for json in runner.firefly.search_transactions("destination_account_starts:amazon no_notes:true")]
    if len(groups) == 0:
        print("No new transaction groups were found.")
        return

    print("Pending transaction groups:\n" + log_tx_groups(groups) + "\n")
    assert all([len(x.transactions) == 1 for x in groups]), f"Unexpected number of transactions (!= 1)"

    for order_id, iterable in groupby(groups, key=lambda x: x.amazon_info.order_id):
        order_groups = list(iterable)

        if process_order(runner, order_id, order_groups):
            print("Updated groups:")
            for group in order_groups:
                print(f"  - {runner.firefly.host}/transactions/show/{group.id}")
            print()

def process_order(runner: Runner, order_id: str, groups: List[TransactionGroup]):
    print(log_separator())
    print(f"{order_id}:\n" + log_tx_groups(groups) + "\n")

    try:
        order = runner.amazon.scrape_order(order_id)
        print("\n" + order.summary + "\n")
    except:
        print(f"[{order_id}] Marking all transaction with ERROR tag because of error:\n{traceback.format_exc()}")
        for group in groups:
            group.add_tags([Tags.ERROR])

            if not runner.args.dry_run:
                runner.firefly.update_transaction(group.id, group.to_json())

        print()
        return True

    if len(groups) != len(order.shipments):
        print(f"! Groups count {len(groups)} != Shipments count {len(order.shipments)}. Probably a pagination issue.\n")
        return False

    unassigned_groups: List[TransactionGroup] = []
    unassigned_shipments = list(order.shipments)

    for group in groups:
        print(log_tx_group(group))
        matched = False

        for index, shipment in enumerate(unassigned_shipments):
            match_exactly = group.amount == shipment.amount
            match_with_promo = group.amount == f"{float(shipment.amount) - order.promotion:.2f}"

            if match_exactly or match_with_promo:
                print(f'~ Matched {"with promotion " if not match_exactly else ""}to\n' + shipment.notes())
                group.set_tags([Tags.MATCH])
                match_tx_group(group, shipment, order.url)

                if runner.args.dry_run:
                    print(log_tx_group(group) + "\n~ PUT: " + str(group.to_json()))
                else:
                    runner.firefly.update_transaction(group.id, group.to_json())

                matched = True
                unassigned_shipments.pop(index)
                print()
                break

        if not matched:
            print("~ No matches\n")
            unassigned_groups.append(group)

    if len(unassigned_groups) == 1 and len(unassigned_shipments) == 1:
        group = unassigned_groups[0]
        shipment = unassigned_shipments[0]
        print(log_tx_group(group) + "\n~ Matched by last_standing rule to\n" + shipment.notes())

        group.set_tags([Tags.LAST])
        match_tx_group(group, shipment, order.url)

        if runner.args.dry_run:
            print(log_tx_group(group) + "\n~ PUT: " + str(group.to_json()))
        else:
            runner.firefly.update_transaction(group.id, group.to_json())

        print()
        return True

    if len(unassigned_groups) > 0:
        remaining_shipment_notes = "\n\n".join([
            f'[All transaction for this order]({runner.firefly.host}/search?search={unassigned_groups[0].amazon_info.original_id})',
            "One of the remaining shipments correspond to this transaction:",
            *[item.notes() for item in unassigned_shipments],
        ])
        print("~ Filling for manual resolution\n\n" + log_tx_groups(unassigned_groups) + "\n<\n" + remaining_shipment_notes + "\n>\n")

        for group in unassigned_groups:
            group.set_tags([Tags.MANUAL, Tags.TODO])

            tx = group.transactions[0]
            tx.external_url = order.url
            tx.notes = remaining_shipment_notes

            if runner.args.dry_run:
                print(log_tx_group(group) + "\n~ PUT: " + str(group.to_json()))
            else:
                runner.firefly.update_transaction(group.id, group.to_json())

        print()

    return True

def match_tx_group(group: TransactionGroup, shipment: AmazonShipment, order_url: str):
    item_count = len(shipment.items)
    tx = group.transactions[0]

    if item_count == 1:
        match_tx(tx, shipment.items[0], order_url, False)
    else:
        set_amount = group.amount == shipment.amount
        if not set_amount:
            print(f"! Group amount {group.amount} doesn't match shipment amount {shipment.amount} and need to be set manually.")
            group.add_tags([Tags.TODO])

        group.group_title = tx.description
        group.transactions.extend([tx.copy() for _ in range(item_count - 1)])
        assert len(group.transactions) == item_count, f"Tx count {len(group.transactions)} != Shipment items count {item_count}"

        for index in range(item_count):
            match_tx(group.transactions[index], shipment.items[index], order_url, set_amount)

def match_tx(tx: Transaction, item: AmazonShipmentItem, order_url: str, set_amount: bool):
    if set_amount:
        tx.amount = item.amount

    tx.external_url = order_url
    tx.internal_reference = f"{item.price_note} @ {item.url}"
    tx.notes = item.name
