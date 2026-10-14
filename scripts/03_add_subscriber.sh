#!/usr/bin/env bash
# Adds the test SIM from your lab config to the Open5GS subscriber database.
# Uses open5gs-dbctl from the Open5GS project. If your MongoDB is inside Docker,
# add the subscriber in the WebUI instead (http://localhost:9999).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
# Reads lab.yaml plus your private configs/lab.local.yaml if it exists
get() { (cd "$HERE/.." && python3 -m e2e.config "$1"); }

IMSI="$(get subscriber.imsi)"
KEY="$(get subscriber.key)"
OPC="$(get subscriber.opc)"
DNN="$(get network.dnn)"

DBCTL="$HERE/.open5gs-dbctl"
if [ ! -x "$DBCTL" ]; then
  curl -fsSL https://raw.githubusercontent.com/open5gs/open5gs/main/misc/db/open5gs-dbctl -o "$DBCTL"
  chmod +x "$DBCTL"
fi

echo "== Adding subscriber IMSI $IMSI on DNN $DNN"
"$DBCTL" add_ue_with_apn "$IMSI" "$KEY" "$OPC" "$DNN"
echo "== The unknown IMSI in your config is deliberately NOT added, so the negative test can check rejection."
