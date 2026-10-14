"""Fetch from Mindbody and print a privacy-safe summary: counts and field names only.

Run with: python -m forma.mindbody_report
Never prints names, emails, phone numbers or any other field values.
"""

import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from forma.mindbody import OPT_IN_FIELD, MindbodyClient, fetch_all

REQUIRED_ENV = [
    "MINDBODY_API_KEY",
    "MINDBODY_SITE_ID",
    "MINDBODY_STAFF_USERNAME",
    "MINDBODY_STAFF_PASSWORD",
]


def field_names(records):
    names = set()
    for record in records:
        names.update(record.keys())
    return sorted(names)


def build_report(result, request_count):
    clients = result["clients"]
    opt_in_present = any(OPT_IN_FIELD in c for c in clients)
    opted_in = sum(1 for c in clients if c.get(OPT_IN_FIELD) is True)
    lines = [
        f"Date range for visits: {result['start_date']} to {result['end_date']}",
        f"Clients fetched: {len(clients)}",
        f"Clients checked for visits and packs: {result['detail_client_count']}",
        f"Visits fetched: {len(result['visits'])}",
        f"Packs/services fetched: {len(result['services'])}",
        f"API requests made: {request_count}",
        f"Opt-in field '{OPT_IN_FIELD}' present: {'YES' if opt_in_present else 'NO'}",
        f"Clients opted in to promotional emails: {opted_in}",
        "",
        "Client fields: " + ", ".join(field_names(clients)),
        "Visit fields: " + ", ".join(field_names(result["visits"])),
        "Pack/service fields: " + ", ".join(field_names(result["services"])),
    ]
    return "\n".join(lines), opt_in_present


def main():
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        print("Missing secrets: " + ", ".join(missing))
        return 1

    limit_text = os.environ.get("CLIENT_LIMIT", "").strip()
    client_limit = int(limit_text) if limit_text else None

    client = MindbodyClient(
        api_key=os.environ["MINDBODY_API_KEY"],
        site_id=os.environ["MINDBODY_SITE_ID"],
        username=os.environ["MINDBODY_STAFF_USERNAME"],
        password=os.environ["MINDBODY_STAFF_PASSWORD"],
    )
    today = datetime.now(ZoneInfo("Europe/London")).date()
    result = fetch_all(client, days=60, today=today, client_limit=client_limit)
    report, opt_in_present = build_report(result, client.request_count)
    print(report)
    return 0 if opt_in_present else 2


if __name__ == "__main__":
    sys.exit(main())
