# This file is assigned to Ethan Guisama, who will format and print the results in the terminal using rich.

"""display.py - print the NetRecon results in the terminal using `rich`.

This file only prints. It calls no APIs and returns nothing.
"""

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich import box

NOT_AVAILABLE = "Not available"  # shared team wording


def _fmt(value):
    """Return `value` ready to print inside a rich table cell.

    Missing values (None or empty text) become a dimmed 'Not available'.
    Real values are wrapped in escape() so stray square brackets in API
    text (for example '[Beta]') cannot break rich's markup.
    """
    if value is None or str(value).strip() == "":
        return f"[dim]{NOT_AVAILABLE}[/dim]"
    text = str(value).strip()
    if text == NOT_AVAILABLE:
        return f"[dim]{NOT_AVAILABLE}[/dim]"
    return escape(text)


def _status_style(status):
    """Pick a colour for the status line (it is only decoration).

    Green when both addresses were found and nothing is missing,
    yellow otherwise. A missing IPv6 is normal, so we never use red.
    """
    text = str(status).lower()
    if "ipv4 and ipv6 detected" in text and "not available" not in text:
        return "green"
    return "yellow"


def display(ipv4, ipv6, meta, status):
    """Print the NetRecon report. Returns nothing.

    ipv4, ipv6 -- an address string, or None
    meta       -- dict with city, region, country, country_code, org, asn
    status     -- a ready-made text line from netrecon.py
    """
    meta = meta or {}  # be safe if someone passes None

    # Two columns: label | value. Labels line up so values are easy to scan.
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()

    def row(label, value):
        """Add one 'Label : value' line."""
        table.add_row(f"{label} :", _fmt(value))

    # Group 1: the addresses (what a technician looks for first)
    row("Public IPv4", ipv4)
    row("Public IPv6", ipv6)
    table.add_row("", "")

    # Group 2: who runs the network
    row("Network / Org", meta.get("org"))
    row("ASN", meta.get("asn"))
    table.add_row("", "")

    # Group 3: where it roughly is
    row("City", meta.get("city"))
    row("Region", meta.get("region"))
    row("Country", meta.get("country"))
    row("Country Code", meta.get("country_code"))
    table.add_row("", "")

    # Last: the one-line summary
    style = _status_style(status)
    table.add_row("[bold cyan]Status :[/bold cyan]",
                  f"[{style}]{escape(str(status))}[/{style}]")

    panel = Panel(
        table,
        title="[bold]NetRecon - Public IP Information[/bold]",
        subtitle="[dim]Location is approximate[/dim]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2),
        expand=False,
    )

    # Created here so rich checks the terminal at print time. Colours turn
    # off by themselves when output is piped or redirected.
    Console().print(panel)