# This file is assigned to Cj Laguardia, who will write the main program that runs detection, metadata and display in order and handles --help

import argparse
import sys

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

    return 0
    
if __name__ == "__main__":
    sys.exit(main())