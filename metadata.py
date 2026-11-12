"""metadata.py - look up location and network details for an IPv4 address.

Uses the free ipwho.is service. Always returns a dictionary with exactly
six keys; anything missing or failed becomes "Not available".
"""

import requests

TIMEOUT = 5  # seconds; shared team rule for every web request
LOOKUP_URL = "https://ipwho.is/{ip}"
NOT_AVAILABLE = "Not available"
KEYS = ("city", "region", "country", "country_code", "org", "asn")


def _empty():
    """Return the six-key dictionary with every value 'Not available'."""
    return {key: NOT_AVAILABLE for key in KEYS}


def _clean(value):
    """Return value as stripped text, or 'Not available' if it is empty."""
    if value is None:
        return NOT_AVAILABLE
    text = str(value).strip()
    return text if text else NOT_AVAILABLE


def get_metadata(ipv4):
    """Look up details for `ipv4` (a string or None).

    Returns a dict with exactly: city, region, country, country_code,
    org, asn. Never raises for expected problems.
    """
    meta = _empty()
    if not ipv4:
        return meta

    try:
        response = requests.get(LOOKUP_URL.format(ip=ipv4), timeout=TIMEOUT)
        response.raise_for_status()          # includes HTTP 429 rate limit
        data = response.json()               # bad JSON -> ValueError
    except (requests.RequestException, ValueError):
        return meta

    # A bad/private IP gives HTTP 200 with "success": false.
    if not isinstance(data, dict) or data.get("success") is not True:
        return meta

    meta["city"] = _clean(data.get("city"))
    meta["region"] = _clean(data.get("region"))
    meta["country"] = _clean(data.get("country"))
    meta["country_code"] = _clean(data.get("country_code"))

    connection = data.get("connection")
    if isinstance(connection, dict):
        # org, falling back to isp
        org = _clean(connection.get("org"))
        if org == NOT_AVAILABLE:
            org = _clean(connection.get("isp"))
        meta["org"] = org

        # asn is a number, shown as "AS15169"
        asn = connection.get("asn")
        if asn is not None and str(asn).strip():
            meta["asn"] = "AS" + str(asn).strip()

    return meta