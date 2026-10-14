#!/usr/bin/env bash
# Builds UERANSIM (simulated 5G UE + gNB) into ~/UERANSIM/build.
set -euo pipefail

DIR="${UERANSIM_DIR:-$HOME/UERANSIM}"
sudo apt update
sudo apt install -y make gcc g++ cmake git libsctp-dev lksctp-tools iproute2

if [ ! -d "$DIR" ]; then
  git clone https://github.com/aligungr/UERANSIM "$DIR"
fi
cd "$DIR"
make -j"$(nproc)"

echo "== Built:"
ls -1 "$DIR/build" | grep -E '^nr-(gnb|ue|cli)$'
