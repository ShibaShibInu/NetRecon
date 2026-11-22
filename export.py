# Owner: Aaron Yumul (Lead Python Developer)
"""Turns NetRecon results into a JSON string (used by --json)."""

import json

NOT_AVAILABLE = "Not available"

META_KEYS = ("city", "region", "country", "country_code", "org", "asn")


def _clean(value):
    """Return `value` as-is, or 'Not available' if it is None or empty."""
    if value is None or value == "":
        return NOT_AVAILABLE
    return value


def build_json(ipv4, ipv6, meta, status):
    """Build the JSON report as a string.

    ipv4, ipv6: a string or None. None becomes "Not available".
    meta: the six-key dictionary from get_metadata (city, region,
          country, country_code, org, asn). Missing keys, empty values
          or a None dictionary become "Not available".
    status: the status text chosen by netrecon.py.

    Returns a JSON string with the keys: ipv4, ipv6, the six metadata
    keys, and status. Makes no network calls and prints nothing.
    """
    if not isinstance(meta, dict):
        meta = {}
    report = {
        "ipv4": _clean(ipv4),
        "ipv6": _clean(ipv6),
    }
    for key in META_KEYS:
        report[key] = _clean(meta.get(key))
    report["status"] = _clean(status)
    return json.dumps(report, indent=2, ensure_ascii=False)
