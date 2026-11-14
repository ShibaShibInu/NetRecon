A small Python command-line tool that shows your computer's public IPv4 and IPv6 address, plus roughly where it is and who runs the network. Made for DEVASC Project Activity 3 (Option 2: IPv4/IPv6 Address Application).

## What it does

Run one command and it shows your public IPv4 and IPv6 address, the network name and ASN, and the city, region and country. If your connection has no IPv6, it says "Not available". The location is only approximate. It is made for network technicians and students who want a quick look at their connection.

## Objectives

- Find the public IPv4 and IPv6 address automatically.
- Show network details for the IPv4 address.
- Display the results clearly in the terminal.
- Handle problems (no IPv6, timeouts, rate limits) without crashing.
- Be documented well enough for another team to continue.

## How it works

`netrecon.py` runs three steps in order:

1. **`detection.py` asks ipify for the public IPv4 and IPv6 address.**
2. **`metadata.py` asks ipwho.is for the network name, ASN and location of the IPv4.**
3. **`display.py` prints the results in the terminal using rich.**

## Requirements

You need Python 3 and an internet connection. On Windows (PowerShell):

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python netrecon.py
```

On macOS or Linux, use `python3 -m venv .venv` and `source .venv/bin/activate` instead. `python netrecon.py --help` shows the usage text.

## Run the tests

```powershell
python -m unittest discover -s tests -t .
```

The tests use fake API replies, so they need no internet.

## Files

| File | What it does | Owner |
|---|---|---|
| `netrecon.py` | The main interface of the program | Cris Laguardia |
| `detection.py` | Finds the device's public IPv4 and IPv6 address using ipify | Aaron Yumul |
| `metadata.py` | Looks up network name, ASN and location using ipwho.is | Aaron Yumul |
| `display.py` | Prints the results in the terminal using rich | Ethan Guisama |
| `tests/` and this README |The unit tests and the documentation | Justin Corpuz |

## Future enhancements

- More command-line options (show only IPv4 or IPv6, hide the network details)
- Add IP lookups for any address the user types in
- Export results to JSON or CSV
- Log history of past lookups
- Small diagnostics (DNS and connectivity)
- Fallback lookup provider
- Installable terminal command
- Compare IPv4 and IPv6 side by side
  
