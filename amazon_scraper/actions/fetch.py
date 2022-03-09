"""Fetches Amazon order info for new transaction groups which don't have notes attached."""

import logging
import traceback
from itertools import groupby
from typing import List

from amazon_scraper.actions.common import *
from amazon_scraper.deps import Runner
from amazon_scraper.firefly.models import *


def run(runner: Runner):
    last_groups = []

    while True:
        keyfunc = lambda x: x.amazon_info.order_id
        groups = runner.firefly.search_transactions(f"{runner.base_query} no_notes:true")
        groups = sorted(groups, key=keyfunc)

        if len(groups) == 0 or groups == last_groups:
            logging.info("No new transaction groups were found.")
            return

        last_groups = groups
        logging.debug(f"Pending transaction groups:\n{format_list(groups)}")
        assert all([len(x.transactions) == 1 for x in groups]), f"Unexpected number of transactions (!= 1)"

        for order_id, iterable in groupby(groups, key=keyfunc):
            order_groups = list(iterable)

            if process_order(order_id, order_groups, runner):
                logging.info(f"[{order_id}] Updated groups:\n{format_tx_urls(order_groups, runner.firefly.host)}")

        if runner.args.dry_run:
            return

def process_order(order_id: str, groups: List[TransactionGroup], runner: Runner):
    logging.info(f"[{order_id}] Processing order:\n{format_tx_groups(groups)}")

    try:
        order = runner.amazon.scrape_order(order_id)
        logging.info(f"[{order_id}] Amazon order summary:\n" + "  " + "\n  ".join(order.summary.split(sep="\n")))
    except:
        logging.info(f"[{order_id}] Order scraping failed with error:\n{traceback.format_exc()}")
        return False

    if len(groups) != len(order.shipments):
        logging.warning(f"[{order_id}] Groups count ({len(groups)}) != Shipments count ({len(order.shipments)}). Probably a pagination issue.")
        return False

    unassigned_groups: List[TransactionGroup] = []
    unassigned_shipments = list(order.shipments)

    for group in groups:
        matched = False

        for index, shipment in enumerate(unassigned_shipments):
            match_exactly = group.amount == shipment.amount
            match_with_promo = group.amount == f"{float(shipment.amount) - order.promotion:.2f}"

            if match_exactly or match_with_promo:
                logging.info(f'{format_tx_group(group)}\n~ Matched {"with promotion " if not match_exactly else ""}to\n{shipment.notes()}')
                group.set_tags([Tags.MATCH])
                match_tx_group(group, shipment, order.url)
                commit_tx_group(group, runner)

                matched = True
                unassigned_shipments.pop(index)
                break

        if not matched:
            logging.info(f"{format_tx_group(group)}\n~ Found no direct matches")
            unassigned_groups.append(group)

    if len(unassigned_groups) == 1 and len(unassigned_shipments) == 1:
        group = unassigned_groups[0]
        shipment = unassigned_shipments[0]
        logging.info(f"{format_tx_group(group)}\n~ Matched by last_standing rule to\n{shipment.notes()}")

        group.set_tags([Tags.LAST])
        match_tx_group(group, shipment, order.url)
        commit_tx_group(group, runner)

        return True

    if len(unassigned_groups) > 0:
        remaining_shipment_notes = "\n\n".join([
            f'[All transaction for this order]({runner.firefly.host}/search?search={unassigned_groups[0].amazon_info.original_id})',
            "One of the remaining shipments correspond to this transaction:",
            *[item.notes() for item in unassigned_shipments],
        ])
        logging.info(f"~ Filling for manual resolution\n\n{format_tx_groups(unassigned_groups)}\n<<<\n{remaining_shipment_notes}\n>>>")

        for group in unassigned_groups:
            group.set_tags([Tags.MANUAL, Tags.TODO])

            tx = group.transactions[0]
            tx.external_url = order.url
            tx.notes = remaining_shipment_notes

            commit_tx_group(group, runner)

    return True

def match_tx_group(group: TransactionGroup, shipment: AmazonShipment, order_url: str):
    item_count = len(shipment.items)
    tx = group.transactions[0]

    if item_count == 1:
        match_tx(tx, shipment.items[0], order_url, False)
    else:
        set_amount = group.amount == shipment.amount
        if not set_amount:
            logging.warning(f"Group amount {group.amount} doesn't match shipment amount {shipment.amount} and need to be set manually.")
            group.add_tags([Tags.TODO])

        group.group_title = tx.description
        group.transactions.extend([tx.copy() for _ in range(item_count - 1)])
        assert len(group.transactions) == item_count, f"Tx count {len(group.transactions)} != Shipment items count {item_count}"

        for index in range(item_count):
            match_tx(group.transactions[index], shipment.items[index], order_url, set_amount)

def commit_tx_group(group: TransactionGroup, runner: Runner):
    if runner.args.dry_run:
        logging.info(f"~ Resulting transaction group:\n{format_tx_group(group)}")
        logging.debug(f"{format_tx_group(group)}\n~ PUT: {str(group.to_json())}")
    else:
        runner.firefly.update_transaction(group)
