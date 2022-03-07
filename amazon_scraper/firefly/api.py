import json

import requests


class FireflyAPI:
    """Firefly API driver."""

    def __init__(self, host, auth_token):
        self.headers = {'Authorization': "Bearer " + auth_token if auth_token is not None else ''}
        self.host = host if host is None or not host.endswith('/') else host[:-1] # Remove trailing backslash
        self.base_url = self.host + '/api/v1' if host is not None else self.host

    def _validated(self, response):
        """Returns valid responses or throws an error, supplying it with response body"""

        try:
            response.raise_for_status()
            return response
        except:
            print(f"\n! Failed response body: {response.json()}")
            raise

    def _get(self, endpoint, params=None):
        """Handles general GET requests."""

        return self._validated(requests.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=self.headers
        ))

    def _post(self, endpoint, payload):
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

    def _put(self, endpoint, payload):
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
        return self._get("/search/transactions", params={
            "query": query,
            "page": page,
        }).json()["data"]

    def update_transaction(self, id, payload):
        return self._put(f"/transactions/{id}", json.dumps(payload))
