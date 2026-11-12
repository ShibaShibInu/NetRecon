# This file is assigned to Aaron Yumul, who will write the functions that get the public IPv4 and IPv6 addresses from ipify.
# Owner: Aaron Yumul
"""detection.py - find this computer's public IPv4 and IPv6 addresses.

Uses the free ipify service. Expected failures (timeout, no IPv6, HTTP
error, bad JSON) return None instead of raising an error.
"""

import ipaddress

import requests

TIMEOUT = 5  # seconds; shared team rule for every web request
IPV4_URL = "https://api.ipify.org?format=json"
IPV6_URL = "https://api6.ipify.org?format=json"


def _fetch_ip(url, version):
    """Ask `url` for our public IP and return it as a string, or None.

    `version` is 4 or 6. The address is only accepted if it really is
    that IP version, so an IPv4 address can never be shown as IPv6.
    """
    try:
        response = requests.get(url, timeout=TIMEOUT)
        response.raise_for_status()          # HTTP errors (4xx/5xx)
        data = response.json()               # bad JSON -> ValueError
        address = ipaddress.ip_address(str(data["ip"]).strip())
    except (requests.RequestException, ValueError, KeyError, TypeError):
        # Timeout, no connection (e.g. no IPv6), HTTP error, bad JSON,
        # missing "ip" key, or text that is not an IP address.
        return None

    if address.version != version:
        return None
    return str(address)


def get_public_ipv4():
    """Return the public IPv4 address as a string, or None."""
    return _fetch_ip(IPV4_URL, 4)


def get_public_ipv6():
    """Return the public IPv6 address as a string, or None."""
    return _fetch_ip(IPV6_URL, 6)