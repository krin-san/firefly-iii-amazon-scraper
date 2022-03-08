from argparse import Namespace

from .amazon.scraper import AmazonScraper
from .firefly.api import FireflyAPI


class AppArgs:
    def __init__(self, args: Namespace):
        self.dry_run: bool = args.dry_run
        self.cache_dir: str = args.cache_dir
        self.log: str = args.log # Optional
        self.log_level: str = args.log_level

class Runner:
    def __init__(self, amazon: AmazonScraper, firefly: FireflyAPI, args: AppArgs):
        self.amazon = amazon
        self.firefly = firefly
        self.args = args
        self.base_query = "destination_account_starts:amazon"
