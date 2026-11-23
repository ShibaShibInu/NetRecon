# Owner: Aaron Yumul (Lead Python Developer)
"""Input validation helpers for NetRecon."""

import ipaddress


def validate_ip(text):
    """Check whether `text` is a valid IPv4 or IPv6 address.

    Takes any value. Returns the cleaned address as a string
    (leading/trailing spaces removed, IPv6 written in its short form)
    if it is a valid IP address. Otherwise returns None.
    Never raises for bad input.
    """
    if not isinstance(text, str):
        return None
    cleaned = text.strip()
    if not cleaned:
        return None
    try:
        return str(ipaddress.ip_address(cleaned))
    except ValueError:
        return None
