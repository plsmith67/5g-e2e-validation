"""Offline checks that the log and ping parsers work. These run without any lab."""
from e2e import net
from e2e.patterns import NG_SETUP_OK, PDU_OK, REGISTRATION_OK, RRC_CONNECTED, TUN_UP, clean


def test_parsers_read_ueransim_logs():
    """Self-check: log patterns recognise UERANSIM output"""
    assert NG_SETUP_OK.search("[ngap] [info] NG Setup procedure is successful")
    assert RRC_CONNECTED.search("[rrc] [info] RRC connection established")
    assert REGISTRATION_OK.search("[nas] [info] Initial Registration is successful")
    assert PDU_OK.search("[nas] [info] PDU Session establishment is successful PSI[1]")
    line = clean("\x1b[32m[app] [info] Connection setup for PDU session[1] is successful, "
                 "TUN interface[uesimtun0, 10.45.0.2] is up.\x1b[0m")
    m = TUN_UP.search(line)
    assert m and m.group("iface") == "uesimtun0" and m.group("ip") == "10.45.0.2"


def test_parsers_read_ping_summary():
    """Self-check: ping parser reads loss and average RTT"""
    r = net.parse_ping("10 packets transmitted, 10 received, 0% packet loss, time 9012ms\n"
                       "rtt min/avg/max/mdev = 11.2/14.8/20.1/2.3 ms")
    assert r.loss_pct == 0.0 and r.avg_ms == 14.8
