# This file is assigned to Cj Laguardia, who will write the main program that runs detection, metadata and display in order and handles --help

import argparse
import contextlib
import io
import ipaddress
import sys

from detection import get_public_ipv4, get_public_ipv6
from metadata import NOT_AVAILABLE, get_metadata
from display import display
from export import build_json
from validation import validate_ip

def pick_status(ipv4, ipv6, meta, no_metadata=False):
    """Make the one-line status text shown at the bottom of the report."""

    # Which addresses did we find?
    if ipv4 and ipv6:
        status = "IPv4 and IPv6 detected"
    elif ipv4:
        status = "IPv4 detected; IPv6 not available"
    else:
        status = "IPv6 detected; IPv4 not available"

    # We have an IPv4 but the lookup came back empty (rate limit, no internet...)
    if ipv4 and not no_metadata and all(value == NOT_AVAILABLE for value in meta.values()):
        status += "; network details not available"
    return status

def show_result(ipv4, ipv6, meta, status, args, options):
    """Print the result as JSON (--json) or as the normal report.

    With -o, the result is saved to a file instead of printed.
    Returns 0 if it worked, 2 if the file could not be written.
    """
    # With -o, catch what would be printed so it can go into the file
    buffer = io.StringIO()
    capture = contextlib.redirect_stdout(buffer) if args.output else contextlib.nullcontext()
    with capture:
        if args.json:
            print(build_json(ipv4, ipv6, meta, status))
        else:
            display(ipv4, ipv6, meta, status, **options)

    if not args.output:
        return 0

    try:
        with open(args.output, "w", encoding="utf-8") as file:
            file.write(buffer.getvalue())
    except OSError as error:
        print(f"Could not save to '{args.output}': {error}", file=sys.stderr)
        return 2
    print(f"Saved to {args.output}")
    return 0

def main():
    """Run NetRecon: find the public IPs, look up details and show them.

    Returns:
        int: 0 if at least one address was found, otherwise 1.
        2 if the address given to --lookup is not valid.
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
    parser.add_argument("-o", "--output", metavar="FILENAME", help="save the results to a text file instead of printing them")
    args = parser.parse_args()
    
    options = {}
    if args.ipv4:
        options["show_ipv6"] = False
    if args.ipv6:
        options["show_ipv4"] = False
    if args.no_metadata:
        options["show_meta"] = False
    
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
        if args.no_metadata:
            # No request when the details are not wanted
            meta = get_metadata(None)
            status = f"Lookup for {address}"
        elif ip.is_global:
            meta = get_metadata(address)
            status = f"Lookup for {address}"
            if all(value == NOT_AVAILABLE for value in meta.values()):
                status += "; network details not available"
        else:
            # No lookup done
            meta = get_metadata(None)
            status = f"Lookup for {address}; private or reserved address, no public details"

            # Show result
        return show_result(ipv4, ipv6, meta, status, args, options)

    # Step 1: find our public addresses (only the one that was asked for)
    ipv4 = None if args.ipv6 else get_public_ipv4()
    ipv6 = None if args.ipv4 else get_public_ipv6()

    # If nothing is found, no display
    if not ipv4 and not ipv6:
        print("No public IP address detected. Check your internet connection.")
        return 1

    # Step 2: look up details (skipped for --no-metadata)
    if args.no_metadata:
        meta = get_metadata(None)
    elif args.ipv6:
        meta = get_metadata(ipv6)
    else:
        meta = get_metadata(ipv4)

    # Status text
    if args.ipv4 or args.ipv6:
        status = "IPv4 detected" if args.ipv4 else "IPv6 detected"
        if not args.no_metadata and all(value == NOT_AVAILABLE for value in meta.values()):
            status += "; network details not available"
    else:
        status = pick_status(ipv4, ipv6, meta, args.no_metadata)

    # Step 3: show results
    return show_result(ipv4, ipv6, meta, status, args, options)

if __name__ == "__main__":
    sys.exit(main())