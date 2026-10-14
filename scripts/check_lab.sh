#!/usr/bin/env bash
# Quick health check before running tests. Read only, changes nothing.
for svc in mongod open5gs-nrfd open5gs-amfd open5gs-ausfd open5gs-udmd open5gs-smfd open5gs-upfd open5gs-pcfd; do
  printf "%-16s %s\n" "$svc" "$(systemctl is-active "$svc" 2>/dev/null || echo missing)"
done
echo
echo "AMF listening on N2 (SCTP 38412):"
ss -lnp --sctp 2>/dev/null | grep 38412 || echo "  not found"
echo
echo "UERANSIM binaries:"
ls -1 "${UERANSIM_DIR:-$HOME/UERANSIM}/build" 2>/dev/null | grep -E '^nr-' || echo "  not built yet"
