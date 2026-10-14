"""Read-only access to the Mindbody Public API (v6).

Fetches clients, their class visits and their packs/services. The only POST
this module ever makes is to log in (issue a staff token); everything else is
a GET, so nothing in Mindbody can be changed from here.
"""

import time
from datetime import date, timedelta

import requests

BASE_URL = "https://api.mindbodyonline.com/public/v6"
PAGE_SIZE = 200  # Mindbody's maximum page size
OPT_IN_FIELD = "SendPromotionalEmails"


class MindbodyError(Exception):
    pass


class MindbodyClient:
    def __init__(self, api_key, site_id, username, password, session=None,
                 base_url=BASE_URL, retry_wait_seconds=2):
        self.api_key = api_key
        self.site_id = str(site_id)
        self.username = username
        self.password = password
        self.session = session or requests.Session()
        self.base_url = base_url
        self.retry_wait_seconds = retry_wait_seconds
        self.token = None
        self.request_count = 0

    def _headers(self):
        headers = {
            "Api-Key": self.api_key,
            "SiteId": self.site_id,
            "Content-Type": "application/json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _send(self, method, path, params=None, json=None):
        """Send one request, retrying up to 3 times if Mindbody says 'slow down' or has a server error."""
        url = f"{self.base_url}/{path}"
        for attempt in range(4):
            self.request_count += 1
            response = self.session.request(
                method, url, headers=self._headers(), params=params, json=json, timeout=30
            )
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < 3:
                    time.sleep(self.retry_wait_seconds * (2 ** attempt))
                    continue
            if response.status_code >= 400:
                # Only the status and Mindbody's error code: the full body could echo client data.
                try:
                    code = response.json().get("Error", {}).get("Code", "unknown")
                except ValueError:
                    code = "unknown"
                raise MindbodyError(f"{method} {path} failed with HTTP {response.status_code} ({code})")
            return response.json()

    def login(self):
        data = self._send(
            "POST", "usertoken/issue",
            json={"Username": self.username, "Password": self.password},
        )
        self.token = data.get("AccessToken")
        if not self.token:
            raise MindbodyError("Login succeeded but no AccessToken was returned")

    def _get(self, path, params=None):
        if not self.token:
            self.login()
        return self._send("GET", path, params=params)

    def _get_all_pages(self, path, result_key, params=None):
        items, offset = [], 0
        while True:
            page = self._get(path, {**(params or {}), "Limit": PAGE_SIZE, "Offset": offset})
            batch = page.get(result_key) or []
            items.extend(batch)
            total = (page.get("PaginationResponse") or {}).get("TotalResults", len(items))
            offset += len(batch)
            if not batch or offset >= total:
                return items

    def get_clients(self):
        return self._get_all_pages("client/clients", "Clients")

    def get_client_visits(self, client_id, start_date, end_date):
        return self._get_all_pages("client/clientvisits", "Visits", {
            "ClientId": client_id,
            "StartDate": start_date.isoformat(),
            "EndDate": end_date.isoformat(),
        })

    def get_client_services(self, client_id):
        """Packs and other services the client has bought, including ExpirationDate."""
        return self._get_all_pages("client/clientservices", "ClientServices", {"ClientId": client_id})


def fetch_all(client, days=60, today=None, client_limit=None):
    """Fetch clients, plus visits (last `days` days) and packs for each client.

    Visits and packs need one request per client, so `client_limit` caps how
    many clients get those extra requests (None = all clients).
    """
    today = today or date.today()
    start = today - timedelta(days=days)
    clients = client.get_clients()
    detail_clients = clients if client_limit is None else clients[:client_limit]

    visits, services = [], []
    for c in detail_clients:
        visits.extend(client.get_client_visits(c["Id"], start, today))
        services.extend(client.get_client_services(c["Id"]))

    return {
        "clients": clients,
        "visits": visits,
        "services": services,
        "detail_client_count": len(detail_clients),
        "start_date": start,
        "end_date": today,
    }
