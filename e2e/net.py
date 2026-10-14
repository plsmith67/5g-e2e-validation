"""Service checks run through the UE's TUN interface, so traffic really crosses N3, the UPF and N6."""
import subprocess
from types import SimpleNamespace

from .patterns import PING_LOSS, PING_RTT


def parse_ping(output: str):
    loss = PING_LOSS.search(output)
    rtt = PING_RTT.search(output)
    return SimpleNamespace(
        loss_pct=float(loss.group("loss")) if loss else 100.0,
        avg_ms=float(rtt.group("avg")) if rtt else None,
        raw=output,
    )


def ping(iface: str, target: str, count: int):
    out = subprocess.run(["ping", "-I", iface, "-c", str(count), "-W", "2", target],
                         capture_output=True, text=True)
    return parse_ping(out.stdout + out.stderr)
