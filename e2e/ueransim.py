"""Start the UERANSIM gNB and UE, write their configs, and watch their logs."""
import shutil
import subprocess
import threading
import time
from pathlib import Path

import yaml

from .patterns import clean


class Proc:
    """A running nr-gnb or nr-ue process. Every log line is kept and saved to a file."""

    def __init__(self, cmd, log_path: Path):
        self.cmd = cmd
        self.log_path = log_path
        self.lines = []
        self._lock = threading.Lock()
        self._log = open(log_path, "w")
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for raw in self.p.stdout:
            line = clean(raw)
            with self._lock:
                self.lines.append(line)
            self._log.write(line + "\n")
            self._log.flush()

    def wait_for(self, pattern, timeout):
        """Return the first regex match in the log, waiting up to `timeout` seconds. None if not seen."""
        end = time.time() + timeout
        seen = 0
        while True:
            with self._lock:
                new = self.lines[seen:]
                seen = len(self.lines)
            for line in new:
                m = pattern.search(line)
                if m:
                    return m
            if time.time() >= end or self.p.poll() is not None and not new:
                return None
            time.sleep(0.2)

    def find(self, pattern):
        with self._lock:
            for line in self.lines:
                if pattern.search(line):
                    return line
        return None

    def tail(self, n=15):
        with self._lock:
            return "\n".join(self.lines[-n:])

    def stop(self):
        if self.p.poll() is None:
            self.p.terminate()
            try:
                self.p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.p.kill()
        self._log.close()


def _binary(cfg, name):
    path = cfg.lab.ueransim_dir / "build" / name
    return path if path.exists() else shutil.which(name)


def binaries_present(cfg):
    return bool(_binary(cfg, "nr-gnb") and _binary(cfg, "nr-ue"))


def _template(cfg, name):
    with open(cfg.lab.ueransim_dir / "config" / name) as f:
        return yaml.safe_load(f)


def write_gnb_config(cfg, out_dir: Path) -> Path:
    """Start from UERANSIM's own open5gs-gnb.yaml and set the values from lab.yaml."""
    c = _template(cfg, "open5gs-gnb.yaml")
    n = cfg.network
    c.update(mcc=n.mcc, mnc=n.mnc, tac=n.tac, linkIp=n.gnb_ip, ngapIp=n.gnb_ip, gtpIp=n.gnb_ip)
    c["amfConfigs"] = [{"address": n.amf_ngap_ip, "port": 38412}]
    c["slices"] = [{"sst": n.sst}]
    path = out_dir / "gnb.yaml"
    path.write_text(yaml.safe_dump(c, sort_keys=False))
    return path


def write_ue_config(cfg, out_dir: Path, name="ue", imsi=None, dnn=None) -> Path:
    """Start from UERANSIM's own open5gs-ue.yaml and set subscriber, PLMN and DNN."""
    c = _template(cfg, "open5gs-ue.yaml")
    n, s = cfg.network, cfg.subscriber
    c.update(supi=f"imsi-{imsi or s.imsi}", mcc=n.mcc, mnc=n.mnc, key=s.key, op=s.opc, opType="OPC",
             gnbSearchList=[n.gnb_ip])
    c["sessions"] = [{"type": "IPv4", "apn": dnn or n.dnn, "slice": {"sst": n.sst}}]
    c["configured-nssai"] = [{"sst": n.sst}]
    c["default-nssai"] = [{"sst": n.sst}]
    path = out_dir / f"{name}.yaml"
    path.write_text(yaml.safe_dump(c, sort_keys=False))
    return path


def start_gnb(cfg, out_dir: Path) -> Proc:
    conf = write_gnb_config(cfg, out_dir)
    return Proc([str(_binary(cfg, "nr-gnb")), "-c", str(conf)], out_dir / "gnb.log")


def start_ue(cfg, out_dir: Path, name="ue", imsi=None, dnn=None) -> Proc:
    conf = write_ue_config(cfg, out_dir, name=name, imsi=imsi, dnn=dnn)
    cmd = [str(_binary(cfg, "nr-ue")), "-c", str(conf)]
    if cfg.lab.use_sudo:
        cmd = ["sudo", "-n"] + cmd   # run `sudo -v` before pytest so this does not prompt
    return Proc(cmd, out_dir / f"{name}.log")
