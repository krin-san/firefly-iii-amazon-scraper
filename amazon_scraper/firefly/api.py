import json
import logging
from typing import Union

import requests
from amazon_scraper.firefly.models.transaction_group import TransactionGroup


class FireflyAPI:
    """Firefly API driver."""

    def __init__(self, host: str, auth_token: str):
        self.headers = {'Authorization': "Bearer " + auth_token if auth_token is not None else ''}
        self.host = host if host is None or not host.endswith('/') else host[:-1] # Remove trailing backslash
        self.base_url = self.host + '/api/v1' if host is not None else self.host

    def _validated(self, response):
        """Returns valid responses or throws an error, supplying it with response body"""

        try:
            response.raise_for_status()
            return response
        except:
            logging.error(f"Error response body: {response.json()}")
            raise

    def _get(self, endpoint: str, params: Union[dict, None] = None):
        """Handles general GET requests."""

        return self._validated(requests.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self.headers
        ))

    def _post(self, endpoint: str, payload: str):
        """Handles general POST requests."""

        return self._validated(requests.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            headers={
                **self.headers,
                **{
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                }
            }
        ))

    def _put(self, endpoint: str, payload: str):
        """Handles general PUT requests."""

        return self._validated(requests.put(
            f"{self.base_url}{endpoint}",
            data=payload,
            headers={
                **self.headers,
                **{
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                }
            }
        ))

    def search_transactions(self, query: str, page: int = 1):
        data = self._get("/search/transactions", params={
            "query": query,
            "page": page,
        }).json()["data"]
        return [TransactionGroup.from_json(json) for json in data]

    def update_transaction(self, group: TransactionGroup):
        return self._put(f"/transactions/{group.id}", json.dumps(group.to_json()))
