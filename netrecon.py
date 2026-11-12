# This file is assigned to Cj Laguardia, who will write the main program that runs detection, metadata and display in order and handles --help

import argparse
import sys

from detection import get_public_ipv4, get_public_ipv6
from metadata import NOT_AVAILABLE, get_metadata
from display import display

def pick_status(ipv4, ipv6, meta):
    """Make the one-line status text shown at the bottom of the report."""
    
    if ipv4 and ipv6:
        status = "IPv4 and IPv6 detected"
    elif ipv4:
        status = "IPv4 detected; IPv6 not available"
    else:
        status = "IPv6 detected; IPv4 not available"
        
    if ipv4 and all(value == NOT_AVAILABLE for value in meta.values()):
        status += "; network details not available"
    return status

def main():
    """Run NetRecon: find the public IPs, look up details and show them.
    
    Returns:
        int: 0 if at least one address was found, otherwise 1.
    """
    parser = argparse.ArgumentParser(
        prog="netrecon",
        description=(
            "Show this device's current public IPv4/IPv6 address and network details."
        ),
        epilog="Note: This tool requires internet access to run"
    )
    
    megroup = parser.add_mutually_exclusive_group()
    megroup.add_argument("--ipv4", action="store_true", help="show only the IPv4 address")
    megroup.add_argument("--ipv6", action="store_true", help="show only the IPv6 address")
    parser.add_argument("--no-metadata", action="store_true", help="don't show the network details")
    args = parser.parse_args()
    
    ipv4 = get_public_ipv4()
    ipv6 = get_public_ipv6()
    
    if not ipv4 and not ipv6:
        print("No public IP address detected. Check your internet connection.")
        return 1
    
    meta = get_metadata(ipv4)
    
    display(ipv4, ipv6, meta, pick_status(ipv4, ipv6, meta))   
    return 0
    
if __name__ == "__main__":
    sys.exit(main())