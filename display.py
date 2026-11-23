# This file is assigned to Ethan Guisama, who will format and print the results in the terminal using rich.

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich import box

NOT_AVAILABLE = "Not available"  # shared team wording


def _fmt(value):

    if value is None or str(value).strip() == "":
        return f"[dim]{NOT_AVAILABLE}[/dim]"
    text = str(value).strip()
    if text == NOT_AVAILABLE:
        return f"[dim]{NOT_AVAILABLE}[/dim]"
    return escape(text)


def _status_style(status):

    text = str(status).lower()
    if "ipv4 and ipv6 detected" in text and "not available" not in text:
        return "green"
    return "yellow"


def display(ipv4, ipv6, meta, status,
            show_ipv4=True, show_ipv6=True, show_meta=True):

    meta = meta or {}  # be safe if someone passes None

    # Two columns: label | value. Labels line up so values are easy to scan.
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold cyan", no_wrap=True)
    table.add_column()

    def row(label, value):
        """Add one 'Label : value' line."""
        table.add_row(f"{label} :", _fmt(value))

    # Group 1: the addresses (what a technician looks for first)
    if show_ipv4:
        row("Public IPv4", ipv4)
    if show_ipv6:
        row("Public IPv6", ipv6)
    if show_ipv4 or show_ipv6:
        table.add_row("", "")  # blank line only if this group was printed

    if show_meta:
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

    Console().print(panel)
