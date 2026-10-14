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


def read_secrets(env):
    """Read the Mindbody secrets, trimming stray spaces or line breaks pasted in with them."""
    return {name: (env.get(name) or "").strip() for name in REQUIRED_ENV}


def secret_format_problems(secrets):
    """Describe malformed secrets without ever revealing their values."""
    problems = []
    for name in ("MINDBODY_API_KEY", "MINDBODY_SITE_ID"):  # these two are sent as HTTP headers
        value = secrets[name]
        if any(ch in value for ch in "\r\n"):
            problems.append(f"{name} contains a line break in the middle")
        if any(ch in value for ch in " \t"):
            problems.append(f"{name} contains a space or tab in the middle")
        if not value.isascii() or not value.isprintable():
            problems.append(f"{name} contains an unusual or invisible character")
    if secrets["MINDBODY_SITE_ID"] and not secrets["MINDBODY_SITE_ID"].lstrip("-").isdigit():
        problems.append("MINDBODY_SITE_ID should be just a number, like -99")
    return problems


def main():
    secrets = read_secrets(os.environ)
    missing = [name for name, value in secrets.items() if not value]
    if missing:
        print("Missing secrets: " + ", ".join(missing))
        return 1
    problems = secret_format_problems(secrets)
    if problems:
        print("Secrets need re-entering in GitHub (values not shown):")
        print("\n".join("- " + p for p in problems))
        return 1

    limit_text = os.environ.get("CLIENT_LIMIT", "").strip()
    client_limit = int(limit_text) if limit_text else None

    client = MindbodyClient(
        api_key=secrets["MINDBODY_API_KEY"],
        site_id=secrets["MINDBODY_SITE_ID"],
        username=secrets["MINDBODY_STAFF_USERNAME"],
        password=secrets["MINDBODY_STAFF_PASSWORD"],
    )
    today = datetime.now(ZoneInfo("Europe/London")).date()
    result = fetch_all(client, days=60, today=today, client_limit=client_limit)
    report, opt_in_present = build_report(result, client.request_count)
    print(report)
    return 0 if opt_in_present else 2


if __name__ == "__main__":
    sys.exit(main())
