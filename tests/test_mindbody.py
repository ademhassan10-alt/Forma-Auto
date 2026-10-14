"""Tests for the Mindbody reader. They use saved fake responses and never call the real API."""

import json
from datetime import date
from pathlib import Path

import pytest

from forma.mindbody import MindbodyClient, MindbodyError, fetch_all
from forma.mindbody_report import build_report, read_secrets

FIXTURES = Path(__file__).parent / "fixtures" / "mindbody"


def load(name):
    return json.loads((FIXTURES / name).read_text())


class FakeResponse:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body

    def json(self):
        return self._body


class FakeSession:
    """Stands in for the internet: answers each request with a saved fake response."""

    def __init__(self, overrides=None):
        self.calls = []
        self.overrides = overrides or {}

    def request(self, method, url, headers=None, params=None, json=None, timeout=None):
        path = url.split("/public/v6/")[1]
        params = params or {}
        self.calls.append({"method": method, "path": path, "headers": headers, "params": params})
        if path in self.overrides:
            return self.overrides[path].pop(0)
        if path == "usertoken/issue":
            return FakeResponse(200, load("token.json"))
        if path == "client/clients":
            page = "clients_page1.json" if params["Offset"] == 0 else "clients_page2.json"
            return FakeResponse(200, load(page))
        if path == "client/clientvisits":
            name = "visits_100001.json" if params["ClientId"] == "100001" else "visits_empty.json"
            return FakeResponse(200, load(name))
        if path == "client/clientservices":
            name = "services_100001.json" if params["ClientId"] == "100001" else "services_empty.json"
            return FakeResponse(200, load(name))
        raise AssertionError(f"Unexpected request: {method} {path}")


def make_client(session):
    return MindbodyClient("fake-key", "-99", "fake-user", "fake-pass", session=session, retry_wait_seconds=0)


def test_logs_in_and_sends_required_headers():
    session = FakeSession()
    make_client(session).get_clients()
    login, first_get = session.calls[0], session.calls[1]
    assert login["path"] == "usertoken/issue"
    assert first_get["headers"]["Api-Key"] == "fake-key"
    assert first_get["headers"]["SiteId"] == "-99"
    assert first_get["headers"]["Authorization"] == "Bearer fake-token-123"


def test_reads_every_page_of_clients():
    clients = make_client(FakeSession()).get_clients()
    assert [c["Id"] for c in clients] == ["100001", "100002", "100003"]


def test_clients_include_opt_in_field():
    clients = make_client(FakeSession()).get_clients()
    assert all("SendPromotionalEmails" in c for c in clients)


def test_fetch_all_gets_visits_for_last_60_days_and_packs():
    session = FakeSession()
    result = fetch_all(make_client(session), days=60, today=date(2026, 10, 14))
    assert len(result["clients"]) == 3
    assert len(result["visits"]) == 2
    assert result["services"][0]["ExpirationDate"] == "2026-10-16T00:00:00"
    visit_call = next(c for c in session.calls if c["path"] == "client/clientvisits")
    assert visit_call["params"]["StartDate"] == "2026-08-15"
    assert visit_call["params"]["EndDate"] == "2026-10-14"


def test_client_limit_caps_per_client_requests():
    session = FakeSession()
    result = fetch_all(make_client(session), today=date(2026, 10, 14), client_limit=1)
    assert result["detail_client_count"] == 1
    visit_calls = [c for c in session.calls if c["path"] == "client/clientvisits"]
    assert len(visit_calls) == 1


def test_never_writes_to_mindbody():
    session = FakeSession()
    fetch_all(make_client(session), today=date(2026, 10, 14))
    non_get = [c["path"] for c in session.calls if c["method"] != "GET"]
    assert non_get == ["usertoken/issue"]


def test_retries_when_rate_limited():
    session = FakeSession(overrides={
        "client/clients": [FakeResponse(429, {}), FakeResponse(200, load("clients_page1.json")),
                           FakeResponse(200, load("clients_page2.json"))],
    })
    clients = make_client(session).get_clients()
    assert len(clients) == 3


def test_error_message_has_no_client_data():
    session = FakeSession(overrides={"usertoken/issue": [FakeResponse(401, load("error_401.json"))]})
    with pytest.raises(MindbodyError) as error:
        make_client(session).get_clients()
    assert str(error.value) == "POST usertoken/issue failed with HTTP 401 (DeniedAccess)"


def test_report_shows_counts_and_field_names_but_no_personal_data():
    session = FakeSession()
    client = make_client(session)
    result = fetch_all(client, today=date(2026, 10, 14))
    report, opt_in_present = build_report(result, client.request_count)
    assert opt_in_present
    assert "Clients fetched: 3" in report
    assert "Visits fetched: 2" in report
    assert "Packs/services fetched: 1" in report
    assert "Clients opted in to promotional emails: 2" in report
    for personal_value in ["Fake", "fake1@example.com", "07000000001", "Reformer", "10 Class Pack"]:
        assert personal_value not in report


def test_secrets_are_trimmed_of_pasted_spaces_and_line_breaks():
    env = {
        "MINDBODY_API_KEY": " key-abc\n",
        "MINDBODY_SITE_ID": "-99\n",
        "MINDBODY_STAFF_USERNAME": "user ",
        "MINDBODY_STAFF_PASSWORD": "\tpass",
    }
    assert read_secrets(env) == {
        "MINDBODY_API_KEY": "key-abc",
        "MINDBODY_SITE_ID": "-99",
        "MINDBODY_STAFF_USERNAME": "user",
        "MINDBODY_STAFF_PASSWORD": "pass",
    }
