#!/bin/bash
# ==============================================================================
# SysmoUSIM-SJS1 Programming Script Template
# Programs programmable USIM cards using pySim-prog with standard 3GPP test credentials
# Reference: Section III-B (USIM Programming and Subscriber Provisioning)
# ==============================================================================

set -euo pipefail

PC_SC_DEV="${1:-0}"
IMSI="${2:-001010000000001}"
ADM_KEY="${3:-}"

if [ -z "$ADM_KEY" ]; then
    echo "Usage: $0 [pcsc_device_idx] [imsi] [adm_key]"
    echo ""
    echo "Example:"
    echo "  $0 0 001010000000001 0000000000000000"
    echo ""
    echo "Note: The ADM key is supplied by your card vendor (Sysmocom)."
    exit 1
fi

KI="00112233445566778899aabbccddeeff"
OPC="000102030405060708090a0b0c0d0e0f"
MCC="001"
MNC="01"
AMF="8000"

echo "[*] Programming SysmoUSIM-SJS1 on PC/SC device $PC_SC_DEV..."
echo "    IMSI:  $IMSI"
echo "    MCC:   $MCC, MNC: $MNC"
echo "    AMF:   0x$AMF"
echo "    Ki:    $KI"
echo "    OPc:   $OPC"

# Execute pySim-prog
python3 -m pySim.prog \
    -p "$PC_SC_DEV" \
    -t sysmoUSIM-SJS1 \
    -a "$ADM_KEY" \
    -x "$MCC" \
    -y "$MNC" \
    -i "$IMSI" \
    -k "$KI" \
    -o "$OPC" \
    --amf "$AMF" \
    --epdgid "epc.mnc0${MNC}.mcc${MCC}.3gppnetwork.org"

echo "[✓] SIM programming completed successfully."
