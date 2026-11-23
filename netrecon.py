# This file is assigned to Cj Laguardia, who will write the main program that runs detection, metadata and display in order and handles --help

import argparse
import ipaddress
import sys

from detection import get_public_ipv4, get_public_ipv6
from metadata import NOT_AVAILABLE, get_metadata
from display import display
from validation import validate_ip

def pick_status(ipv4, ipv6, meta):
    """Make the one-line status text shown at the bottom of the report."""

    # Which addresses did we find?
    if ipv4 and ipv6:
        status = "IPv4 and IPv6 detected"
    elif ipv4:
        status = "IPv4 detected; IPv6 not available"
    else:
        status = "IPv6 detected; IPv4 not available"

    # We have an IPv4 but the lookup came back empty (rate limit, no internet...)
    if ipv4 and all(value == NOT_AVAILABLE for value in meta.values()):
        status += "; network details not available"
    return status


def main():
    """Run NetRecon: find the public IPs, look up details and show them.

    Returns:
        int: 0 if at least one address was found, otherwise 1.
        2 if the address given to --loop is not valid.
    """
    parser = argparse.ArgumentParser(
        prog="netrecon",
        description=(
            "Show this device's current public IPv4/IPv6 address and network details."
        ),
        epilog="Note: This tool requires internet access to run"
    )

    # Held for future implementations
    megroup = parser.add_mutually_exclusive_group()
    # --ipv4 and --ipv6 are mutually exclusive and cannot be used together as it makes the tool useless by output
    megroup.add_argument("--ipv4", action="store_true", help="show only the IPv4 address")
    megroup.add_argument("--ipv6", action="store_true", help="show only the IPv6 address")
    megroup.add_argument("--lookup", metavar="IP_ADDRESS", help="look up an IPv4 or IPv6 address you type instead of your own")
    
    parser.add_argument("--no-metadata", action="store_true", help="don't show the network details")
    parser.add_argument("--json", action="store_true", help="print the results as JSON instead of the formatted report")
    args = parser.parse_args()
    
    # --lookup command
    if args.lookup:
        #  Check if it is a valid IP address
        address = validate_ip(args.lookup)
        if address is None:
            print(f"'{args.lookup}' is not a valid IP address.", file=sys.stderr)
            return 2
        
        # Determine if its IPv4 or IPv6
        ip = ipaddress.ip_address(address)
        if ip.version == 4:
            ipv4, ipv6 = address, None
        else:
            ipv4, ipv6 = None, address
        
        # Check if address is public or private
        if ip.is_global:

            meta = get_metadata(address)
            status = f"Lookup for {address}"
            if all(value == NOT_AVAILABLE for value in meta.values()):
                status += "; network details not available"
        else:
            # No lookup done
            meta = get_metadata(None)
            status = f"Lookup for {address}; private or reserved address, no public details"

        # Display result
        display(ipv4, ipv6, meta, status)
        return 0

    # No options yet, but this line is what makes --help work
    parser.parse_args()

    # Step 1: find our public addresses
    ipv4 = get_public_ipv4()
    ipv6 = get_public_ipv6()

    # If nothing is found at all, so there is nothing to show
    if not ipv4 and not ipv6:
        print("No public IP address detected. Check your internet connection.")
        return 1

    # Step 2: look up details for the IPv4 address
    meta = get_metadata(ipv4)

    # Step 3: show results
    display(ipv4, ipv6, meta, pick_status(ipv4, ipv6, meta))
    return 0


if __name__ == "__main__":
    sys.exit(main())