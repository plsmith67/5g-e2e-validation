"""Happy path: one device goes through Radio, Trust, Session and Service on 5G SA."""
import ipaddress

import pytest

from e2e import net
from e2e.patterns import NG_SETUP_OK, PDU_OK, REGISTRATION_OK, RRC_CONNECTED, TUN_UP


def test_radio_gnb_connects_to_amf(gnb, th):
    """Radio: gNB completes NG Setup with the AMF over N2"""
    assert gnb.wait_for(NG_SETUP_OK, th.gnb_ng_setup), "No NG Setup. Is Open5GS running and is amf_ngap_ip right?\n" + gnb.tail()


def test_radio_ue_rrc_connected(ue, gnb, th):
    """Radio: UE sets up an RRC connection with the gNB"""
    assert gnb.wait_for(RRC_CONNECTED, th.rrc_connected), "No RRC connection.\n" + ue.tail()


def test_trust_ue_registers(ue, th):
    """Trust: UE registers on the 5G core (authentication and security pass)"""
    assert ue.wait_for(REGISTRATION_OK, th.registration), (
        "Registration did not succeed. Check the subscriber exists in Open5GS and K/OPc match.\n" + ue.tail())


def test_session_pdu_session_up(ue, th):
    """Session: PDU session is established on the configured DNN"""
    assert ue.wait_for(PDU_OK, th.pdu_session), "No PDU session.\n" + ue.tail()


def test_session_ip_from_correct_pool(ue, cfg, th):
    """Session: UE gets an IP address from the expected pool"""
    m = ue.wait_for(TUN_UP, th.pdu_session)
    assert m, "TUN interface never came up.\n" + ue.tail()
    ip = ipaddress.ip_address(m.group("ip"))
    pool = ipaddress.ip_network(cfg.network.ip_pool)
    assert ip in pool, f"UE got {ip}, expected an address in {pool}"


def test_service_ping_through_upf(ue, th):
    """Service: data reaches the internet through the UPF with acceptable loss and latency"""
    m = ue.wait_for(TUN_UP, th.pdu_session)
    if not m:
        pytest.fail("No TUN interface, so there is no data path to test.")
    r = net.ping(m.group("iface"), th.ping_target, th.ping_count)
    assert r.loss_pct <= th.max_loss_pct, f"Packet loss {r.loss_pct}% (limit {th.max_loss_pct}%)\n{r.raw}"
    assert r.avg_ms is not None and r.avg_ms <= th.max_avg_rtt_ms, f"Average RTT {r.avg_ms} ms (limit {th.max_avg_rtt_ms} ms)"
