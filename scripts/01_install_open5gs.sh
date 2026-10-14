#!/usr/bin/env bash
# Installs MongoDB and Open5GS (4G + 5G core) on Ubuntu 22.04 or 24.04, then turns on NAT
# so UE traffic can leave the UPF to the internet.
# Skip this script if you will reuse the Open5GS already running in your O-RAN lab.
set -euo pipefail

if ! pidof systemd >/dev/null; then
  echo "systemd is not running. On WSL2 add this to /etc/wsl.conf, then run 'wsl --shutdown' in Windows:"
  echo "  [boot]"
  echo "  systemd=true"
  exit 1
fi

. /etc/os-release
echo "== Installing MongoDB 8.0 for Ubuntu ${VERSION_CODENAME}"
sudo apt update
sudo apt install -y gnupg curl software-properties-common
curl -fsSL https://pgp.mongodb.com/server-8.0.asc | sudo gpg --yes -o /usr/share/keyrings/mongodb-server-8.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg ] https://repo.mongodb.org/apt/ubuntu ${VERSION_CODENAME}/mongodb-org/8.0 multiverse" \
  | sudo tee /etc/apt/sources.list.d/mongodb-org-8.0.list
sudo apt update
sudo apt install -y mongodb-org
sudo systemctl enable --now mongod

echo "== Installing Open5GS"
sudo add-apt-repository -y ppa:open5gs/latest
sudo apt update
sudo apt install -y open5gs

echo "== Enabling NAT for the UE pool 10.45.0.0/16"
sudo sysctl -w net.ipv4.ip_forward=1
sudo iptables -t nat -C POSTROUTING -s 10.45.0.0/16 ! -o ogstun -j MASQUERADE 2>/dev/null \
  || sudo iptables -t nat -A POSTROUTING -s 10.45.0.0/16 ! -o ogstun -j MASQUERADE

echo "== Done. Check the core with: scripts/check_lab.sh"
