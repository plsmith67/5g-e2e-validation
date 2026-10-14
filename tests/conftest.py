"""Shared setup: one gNB for the whole run, a fresh UE per test file, and a PASS/FAIL summary at the end."""
import time
from pathlib import Path

import pytest

from e2e import config, ueransim

RUN_DIR = Path(__file__).resolve().parent.parent / "results" / time.strftime("%Y%m%d-%H%M%S")
_docs, _results = {}, []


@pytest.fixture(scope="session")
def cfg():
    return config.load()


@pytest.fixture(scope="session")
def th(cfg):
    return cfg.thresholds


@pytest.fixture(scope="session")
def run_dir():
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    return RUN_DIR


@pytest.fixture(scope="session")
def gnb(cfg, run_dir):
    if not ueransim.binaries_present(cfg):
        pytest.skip(f"UERANSIM not found in {cfg.lab.ueransim_dir}/build. Run scripts/02_install_ueransim.sh first.")
    proc = ueransim.start_gnb(cfg, run_dir)
    yield proc
    proc.stop()


@pytest.fixture(scope="module")
def ue(cfg, run_dir, gnb, th):
    from e2e.patterns import NG_SETUP_OK
    if not gnb.wait_for(NG_SETUP_OK, th.gnb_ng_setup):
        pytest.fail("gNB never connected to the AMF, so the UE cannot be tested.\n" + gnb.tail())
    proc = ueransim.start_ue(cfg, run_dir, name="ue")
    yield proc
    proc.stop()


# ---------- PASS/FAIL summary ----------

def pytest_collection_modifyitems(items):
    for item in items:
        doc = (item.function.__doc__ or item.name).strip().splitlines()[0]
        _docs[item.nodeid] = doc


def pytest_runtest_logreport(report):
    if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
        _results.append((_docs.get(report.nodeid, report.nodeid), report.outcome.upper()))


def pytest_terminal_summary(terminalreporter):
    if not _results:
        return
    label = {"PASSED": "PASS", "FAILED": "FAIL", "SKIPPED": "SKIP"}
    lines = ["", "5G SA end-to-end validation", "=" * 60]
    lines += [f"  {label.get(r, r):5} {name}" for name, r in _results]
    lines.append("=" * 60)
    lines.append("Config: " + " + ".join(p.name for p in config.sources()))
    if RUN_DIR.exists():
        lines.append(f"Logs and configs saved in {RUN_DIR}")
        (RUN_DIR / "summary.md").write_text(
            "| Result | Check |\n|---|---|\n" + "\n".join(f"| {label.get(r, r)} | {n} |" for n, r in _results) + "\n")
    terminalreporter.write_line("\n".join(lines))
