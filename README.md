# 5G SA End-to-End Validation

An automated PASS/FAIL test suite for a 5G standalone network. A simulated IoT device (UERANSIM) connects to a 5G core (Open5GS), and Python tests check every phase of the journey:

| Phase | What gets checked |
|---|---|
| **Radio** | The gNB connects to the AMF (NG Setup) and the UE gets an RRC connection |
| **Trust** | The UE registers, which means authentication and security passed |
| **Session** | A PDU session comes up on the right DNN with an IP from the right pool |
| **Service** | Data reaches the internet through the UPF with acceptable loss and latency |
| **Negative** | An unknown SIM is rejected, and a request for the wrong DNN is rejected |

Everything runs in software on one Ubuntu machine. No radio hardware is needed or used.

> **Status:** the test logic has been checked against simulated UERANSIM logs. The first full run against a live Open5GS lab is in progress.

## What you need

* Windows 11 with WSL2 running **Ubuntu 22.04 or 24.04** (an Ubuntu VM also works)
* **systemd turned on** in WSL2. Check `/etc/wsl.conf` contains:
  ```
  [boot]
  systemd=true
  ```
  If you add it, run `wsl --shutdown` in Windows PowerShell and reopen Ubuntu.
* SCTP support, which the AMF uses on N2. Check with `checksctp` after step 2. Your O-RAN lab already uses SCTP for E2, so this is likely fine.

## Setup (about 30 to 60 minutes, one time)

Run these inside Ubuntu, from the repo folder.

**1. Install the 5G core**
```bash
bash scripts/01_install_open5gs.sh
```
> Already running Open5GS in another lab? Skip this step and reuse it. Put that core's values in a private `configs/lab.local.yaml` (see **Private lab settings** below). Don't run two cores at the same time, because they use the same ports.

**2. Build the simulated device and gNB**
```bash
bash scripts/02_install_ueransim.sh
```

**3. Add the test SIM to the core**
```bash
bash scripts/03_add_subscriber.sh
```

**4. Install the Python test tools**
```bash
sudo apt install -y python3-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**5. Check the lab is healthy**
```bash
bash scripts/check_lab.sh
```
Every Open5GS service should say `active`, and the AMF should be listening on 38412.

## Private lab settings

`configs/lab.yaml` holds safe public defaults and is committed. To test a core whose details should stay private, keep your real values in a local file that Git never uploads:

```bash
cp configs/lab.local.example.yaml configs/lab.local.yaml
```

Edit `configs/lab.local.yaml` and keep only the settings that differ, such as your PLMN, AMF address, DNN, IP pool or SIM values. When the file exists, the tests and `03_add_subscriber.sh` use it automatically, and the test summary shows which config was used. Any `*.local.yaml` file in `configs/` is ignored by Git.

To use a different file for one run:
```bash
LAB_CONFIG=~/my-other-lab.yaml pytest
```

Before pushing, `git status` should never list `lab.local.yaml`.

## Run the tests

```bash
source .venv/bin/activate
sudo -v        # the simulated UE needs root to create its network interface
pytest
```

The suite starts the gNB and UE for you, runs every check, and stops them at the end. It does not change your core configuration.

## What a good run looks like

```
5G SA end-to-end validation
============================================================
  PASS  Self-check: log patterns recognise UERANSIM output
  PASS  Self-check: ping parser reads loss and average RTT
  PASS  Radio: gNB completes NG Setup with the AMF over N2
  PASS  Radio: UE sets up an RRC connection with the gNB
  PASS  Trust: UE registers on the 5G core (authentication and security pass)
  PASS  Session: PDU session is established on the configured DNN
  PASS  Session: UE gets an IP address from the expected pool
  PASS  Service: data reaches the internet through the UPF with acceptable loss and latency
  PASS  Trust (negative): a SIM that is not provisioned cannot register
  PASS  Session (negative): a request for a DNN the subscriber does not have is rejected
============================================================
```

Every run saves its evidence in `results/<date-time>/`: the gNB and UE logs, the exact configs used, and `summary.md`. There's also `results/junit.xml`, which CI tools like Jenkins and GitLab can read.

## When something fails

Each failure message tells you where to look. The most common ones:

| Fails at | Usually means |
|---|---|
| NG Setup | Open5GS AMF isn't running, or `amf_ngap_ip` is wrong |
| Registration | The SIM isn't in the database, or the key or OPc doesn't match |
| PDU session | The DNN or slice in `lab.yaml` doesn't match the subscriber |
| Ping | NAT isn't on (re-run the NAT lines in step 1), or a firewall is blocking traffic |

To watch the real signalling, capture on the loopback interface while the tests run:
```bash
sudo tshark -i lo -f "sctp or udp port 2152 or udp port 8805" -w results/run.pcap
```
Open the file in Wireshark and filter on `ngap`, `nas-5gs` or `pfcp`.

## Repo layout

| Path | What it is |
|---|---|
| `configs/lab.yaml` | Public default settings and pass thresholds |
| `configs/lab.local.yaml` | Your private lab values (you create it, Git ignores it) |
| `e2e/` | Helpers that start UERANSIM, read its logs and run ping |
| `e2e/patterns.py` | The log lines each check looks for |
| `tests/` | The test cases, named by phase |
| `scripts/` | Install, subscriber and health check scripts |
| `results/` | Logs and reports from each run (Git ignores it) |

## Next steps

* Add a throughput test with iperf3 through the UE interface
* Add a second subscriber on a different DNN or slice, and test that the two can't reach each other (segmentation)
* Run the suite from CI after every config change
* Point it at the O-RAN lab gNB and use it as the **Verify** step in the Autonomous RAN loop

## License

MIT. See [LICENSE](LICENSE). The SIM key and OPc in `configs/lab.yaml` are UERANSIM's public test values. Never commit real SIM keys or credentials.
