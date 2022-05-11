This tool allows you to automatically fill in Amazon transaction details by scraping order details from Amazon website.

Adding automation rules on transaction update allows to automatically set appropriate Budget and/or Category for frequently ordered items or subscriptions.

# How it works?

## fetch command

It fetches transactions from Firefly III which don't have attached notes (to skip processed items) and which destination account starts from keyword `amazon`. These transactions are then grouped by Amazon OrderID which is extracted from the transaction description. For each group of transactions an Amazon order webpage is scrapped and parsed. At this point the amount of transactions in a groups should match the amount of order shipments, otherwise the group is skipped until all order transactions can be found on a single Firefly III search page.

Amazon doesn't provide verbose enough order details to match transactions to shipments so the tool uses ordered item prices to try and match them. Order of operations:
- Transactions with prices matching shipment prices are matched with `amazon_match` tag;
- A single last transaction matches to a single last shipment with `amazon_match_last` tag;
- Transactions with multiple items which price matches shipment price are automatically split with corresponding item prices set;
- Transactions with multiple items which price differs from shipment price are automatically split and marked with `amazon_todo` tag without setting item prices;
- If there are any remaining transactions left, they are filled with order details and tagged with `amazon_todo` and `amazon_manual` tags for manual splitting.

When processing is finished it is advised to open `amazon_todo` tag from Firefly III's /tags page and manually resolve all matching transactions removing that tag.

# Usage

Rename `.env.example` file to `.env` and add connection details both for Amazon and Firefly.

Perform a dry run to ensure Amazon scraper can login to your account and to check if Firefly transaction changes look good to you. In dry run mode tool will process just the first page full of Amazon transactions from Firefly and won't commit any changes.
```bash
python3 -m amazon_scraper --log-level DEBUG --dry-run fetch
```

When ready, run tool in normal mode to process all transactions:
```bash
python3 -m amazon_scraper fetch
```

# Requirements

* Python >= 3.8 (tested on 3.8.12 and 3.9.12)
* `geckodriver` installed and and in your `PATH`
* Python packages:
  * `python-dotenv` – for storing connection details
  * `requests` – for REST API interactions with Firefly III
  * `selenium` – for website interactions and scraping
  * `beautifulsoup4` and `lxml` – for order page parsing

All packages can with installed with the following command:
```bash
pip3 install python-dotenv requests selenium beautifulsoup4 lxml
```

# Contributing

If you see a bug and you can fix it yourself, please open a PR, otherwise feel free to open an issue for it.

If you'd like to add a new feature, feel free to do that. I found Jupyter Notebook pretty useful developing or trying out new things so you can start shaping your new actions using the `amazon.ipynb` notebook. Before opening PR please ensure that all tests succeed with `python3 -m unittest tests/*.py`.

# License

This work [is licensed](https://github.com/krin-san/firefly-iii-amazon-scraper/blob/main/LICENSE) under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.html).
