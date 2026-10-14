"""Log lines UERANSIM prints at each step. Kept in one place so they are easy to adjust."""
import re

ANSI = re.compile(r"\x1b\[[0-9;]*m")

# Radio
NG_SETUP_OK = re.compile(r"NG Setup procedure is successful")
RRC_CONNECTED = re.compile(r"RRC connection established")

# Trust
REGISTRATION_OK = re.compile(r"Initial Registration is successful")
REGISTRATION_FAIL = re.compile(r"registration (reject|failed)|Registration Reject", re.I)

# Session
PDU_OK = re.compile(r"PDU Session establishment is successful")
PDU_FAIL = re.compile(r"PDU Session Establishment Reject|PDU Session establishment (procedure )?failed", re.I)
TUN_UP = re.compile(r"TUN interface\[(?P<iface>[^,\]]+),\s*(?P<ip>[0-9.]+)\] is up")

# Service (Linux ping summary)
PING_LOSS = re.compile(r"(?P<loss>[0-9.]+)% packet loss")
PING_RTT = re.compile(r"= [0-9.]+/(?P<avg>[0-9.]+)/[0-9.]+")


def clean(line: str) -> str:
    return ANSI.sub("", line).rstrip()
