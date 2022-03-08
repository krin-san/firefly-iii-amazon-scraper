import json
import logging
import traceback

from amazon_scraper.amazon.cache import FileCache
from amazon_scraper.amazon.driver import AmazonDriver
from amazon_scraper.amazon.models import AmazonOrder
from bs4 import BeautifulSoup


class AmazonScraper:
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        cache_dir: str,
    ):
        self.host = host if host is None or not host.endswith('/') else host[:-1] # Remove trailing backslash
        self.cache = FileCache(cache_dir)
        self.setup_driver = lambda: self._setup_driver(user, password)

    def _setup_driver(self, user: str, password: str):
        self.driver = AmazonDriver()
        self.driver.login(self.host, user, password)

    def _fetch_url(self, url: str):
        return self.driver.get_url(url)

    def scrape_order(self, order_id: str):
        cache = self.cache.get(f"{order_id}.json")
        if cache is not None:
            try:
                logging.debug(f"[{order_id}] Loading order from cache")
                return AmazonOrder.from_json(json.loads(cache))
            except:
                logging.error(f"[{order_id}] Loading from cache failed with error:\n{traceback.format_exc()}")
                pass

        if "br" not in self.__dict__:
            logging.debug("Setting up Selenium driver and logging in...")
            self.setup_driver()
            self.setup_driver = lambda: None

        url = f"{self.host}/gp/your-account/order-details?orderID={order_id}"
        html = self._fetch_url(url)

        try:
            soup = BeautifulSoup(html, "lxml")
            # self.soup = soup

            # div#a-page div#orderDetails
            details = soup.select_one("div#orderDetails")
            assert details is not None, "No #orderDetails section found"
            order = AmazonOrder.from_details(details, url, self.host)

            self.cache.remove(f"{order_id}.html")
            self.cache.add(f"{order_id}.json", order.to_json())

            return order
        except:
            logging.error(f"[{order_id}] Loading from server failed with error:\n{traceback.format_exc()}")
            self.cache.add(f"{order_id}.html", html)
            raise
