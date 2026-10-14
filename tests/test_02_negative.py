"""Negative tests: the network must say no when it should."""
import pytest

from e2e import ueransim
from e2e.patterns import NG_SETUP_OK, PDU_FAIL, PDU_OK, REGISTRATION_FAIL, REGISTRATION_OK


@pytest.fixture
def ready_gnb(gnb, th):
    if not gnb.wait_for(NG_SETUP_OK, th.gnb_ng_setup):
        pytest.fail("gNB is not connected to the AMF.\n" + gnb.tail())
    return gnb


def test_unknown_subscriber_is_rejected(ready_gnb, cfg, run_dir, th):
    """Trust (negative): a SIM that is not provisioned cannot register"""
    ue = ueransim.start_ue(cfg, run_dir, name="ue-unknown-imsi", imsi=cfg.negative.unknown_imsi)
    try:
        ok = ue.wait_for(REGISTRATION_OK, th.negative_wait)
        assert not ok, "An unprovisioned IMSI registered. Subscriber control is not working."
        reject = ue.find(REGISTRATION_FAIL)
        print("Network response:", reject or "no explicit reject seen, registration timed out")
    finally:
        ue.stop()


def test_wrong_dnn_is_rejected(ready_gnb, cfg, run_dir, th):
    """Session (negative): a request for a DNN the subscriber does not have is rejected"""
    ue = ueransim.start_ue(cfg, run_dir, name="ue-wrong-dnn", dnn=cfg.negative.wrong_dnn)
    try:
        ok = ue.wait_for(PDU_OK, th.negative_wait)
        assert not ok, f"PDU session came up on '{cfg.negative.wrong_dnn}'. DNN control is not working."
        reject = ue.find(PDU_FAIL)
        print("Network response:", reject or "no explicit reject seen, PDU session timed out")
    finally:
        ue.stop()
