#!/bin/bash
# ==============================================================================
# Comprehensive Cellular & IMS Diagnostic Utility
# Analyzes SIP signaling, IPsec XFRM policies/SAs, ESP tunnel counts,
# CSCF core container logs, and Android logcat / telephony registry states.
# Reference: Section III-E (COTS UE Activation and Automated Test Harness)
# ==============================================================================

set -euo pipefail

PCAP_FILE=""
OUTPUT_DIR=""
PHONE1_ID="${ADB_DEV1:-}"
PHONE2_ID="${ADB_DEV2:-}"

# Parse optional arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --pcap|-p)
            PCAP_FILE="$2"
            shift 2
            ;;
        --output-dir|-o)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --dev1)
            PHONE1_ID="$2"
            shift 2
            ;;
        --dev2)
            PHONE2_ID="$2"
            shift 2
            ;;
        *)
            if [ -f "$1" ]; then
                PCAP_FILE="$1"
            elif [ -d "$1" ]; then
                OUTPUT_DIR="$1"
            fi
            shift
            ;;
    esac
done

# Fallback auto-detection for devices
if [ -z "$PHONE1_ID" ] || [ -z "$PHONE2_ID" ]; then
    DEVICES=($(adb devices 2>/dev/null | grep -w "device" | awk '{print $1}'))
    if [ "${#DEVICES[@]}" -ge 2 ]; then
        PHONE1_ID="${PHONE1_ID:-${DEVICES[0]}}"
        PHONE2_ID="${PHONE2_ID:-${DEVICES[1]}}"
    else
        PHONE1_ID="${PHONE1_ID:-DEVICE_1_SERIAL}"
        PHONE2_ID="${PHONE2_ID:-DEVICE_2_SERIAL}"
    fi
fi

echo "=============================================================================="
echo " IMS / VoLTE Cellular Forensic Diagnostic Utility"
echo " Components: SIP Signaling • IPsec ESP • Kernel XFRM • CSCF Logs • Android Telephony"
echo "=============================================================================="
[ -n "$PCAP_FILE" ] && echo " PCAP Source: $PCAP_FILE"
echo " Device 1:   $PHONE1_ID"
echo " Device 2:   $PHONE2_ID"
echo "=============================================================================="

# ------------------------------------------------------------------------------
# 1. SIP Call Flow Analysis (tshark)
# ------------------------------------------------------------------------------
echo ""
echo "[1/5] SIP Call Flow & Transport Port Analysis:"
if [ -n "$PCAP_FILE" ] && [ -f "$PCAP_FILE" ]; then
    if command -v tshark >/dev/null 2>&1; then
        tshark -r "$PCAP_FILE" -Y "sip" -T fields \
            -e frame.number -e frame.time_relative -e ip.src -e ip.dst -e ip.proto \
            -e tcp.srcport -e tcp.dstport -e udp.srcport -e udp.dstport \
            -e sip.Method -e sip.Status-Code -e sip.Status-Line 2>/dev/null | awk '
            {
                proto = ($5 == 6) ? "TCP" : "UDP";
                sport = ($5 == 6) ? $6 : $8;
                dport = ($5 == 6) ? $7 : $9;
                method = $10;
                status = ($11 != "") ? ($11 " " $12 " " $13) : method;
                printf "      Frame %4s (+%6.3fs): %15s:%-5s -> %15s:%-5s [%s] %s\n", $1, $2, $3, sport, $4, dport, proto, status;
            }' || true

        echo ""
        echo "      Checking ephemeral port violations (> 10000 on P-CSCF):"
        VIOLATIONS=$(tshark -r "$PCAP_FILE" -Y "sip and ip.src == 172.22.0.21 and (tcp.srcport > 10000 or udp.srcport > 10000)" \
            -T fields -e frame.number -e ip.dst -e tcp.srcport -e tcp.dstport -e udp.srcport -e udp.dstport -e sip.Method 2>/dev/null || true)
        if [ -n "$VIOLATIONS" ]; then
            echo "$VIOLATIONS" | awk '{
                sport = ($3 != "") ? $3 : $5;
                dport = ($4 != "") ? $4 : $6;
                printf "      [!] Frame %s from ephemeral port %s -> %s:%s (%s) will bypass IPsec XFRM!\n", $1, sport, $2, dport, $7;
            }'
        else
            echo "      ✓ No ephemeral source port violations detected on P-CSCF."
        fi
    else
        echo "      [!] tshark not installed; skipping packet trace dissection."
    fi
else
    echo "      [i] No PCAP trace provided; skipping offline SIP flow dissection."
fi

# ------------------------------------------------------------------------------
# 2. ESP / IPsec Traffic Encapsulation Counts
# ------------------------------------------------------------------------------
echo ""
echo "[2/5] ESP / IPsec Tunnel Encapsulation Packet Counts:"
if [ -n "$PCAP_FILE" ] && [ -f "$PCAP_FILE" ] && command -v tshark >/dev/null 2>&1; then
    ESP_TOTAL=$(tshark -r "$PCAP_FILE" -Y "esp" 2>/dev/null | wc -l || echo 0)
    echo "      Total Encapsulated ESP Packets in Trace: $ESP_TOTAL"
else
    echo "      [i] No PCAP trace provided; skipping ESP packet counting."
fi

# ------------------------------------------------------------------------------
# 3. Kernel IPsec XFRM Policies and Security Associations (SAs)
# ------------------------------------------------------------------------------
echo ""
echo "[3/5] Active P-CSCF Kernel IPsec XFRM Policies & SAs:"
if docker ps -q -f name=pcscf | grep -q .; then
    echo "      Active IPsec SAs (ip xfrm state):"
    docker exec pcscf ip xfrm state 2>/dev/null | grep -E "src|proto|spi|mode" | head -n 12 | while IFS= read -r line; do
        echo "        $line"
    done || echo "        None found."

    echo ""
    echo "      Active IPsec Policies (ip xfrm policy):"
    docker exec pcscf ip xfrm policy 2>/dev/null | grep -E "src|dst|dir|priority" | head -n 12 | while IFS= read -r line; do
        echo "        $line"
    done || echo "        None found."
else
    echo "      [!] P-CSCF container is not running."
fi

# ------------------------------------------------------------------------------
# 4. Core Container Signaling Logs
# ------------------------------------------------------------------------------
echo ""
echo "[4/5] Core Container Signaling Logs (Recent):"
for container in pcscf scscf mme; do
    if docker ps -q -f name="$container" | grep -q .; then
        echo "      Recent logs for $container (signaling events):"
        docker logs "$container" --tail 50 2>&1 | grep -i -E "INVITE|REGISTER|200 OK|401|404|503|ipsec|Security-Server|Attach" | tail -n 6 | while IFS= read -r l; do
            echo "        $l"
        done || true
    else
        echo "      [!] Container $container not active."
    fi
done

# ------------------------------------------------------------------------------
# 5. Android Telephony State & Logcat
# ------------------------------------------------------------------------------
echo ""
echo "[5/5] Android Telephony State & Diagnostic Dumps:"
if command -v adb >/dev/null 2>&1; then
    for dev in "$PHONE1_ID" "$PHONE2_ID"; do
        if adb -s "$dev" get-state >/dev/null 2>&1; then
            echo "      Device $dev Telephony Registry:"
            adb -s "$dev" shell dumpsys telephony.registry 2>/dev/null | grep -E "mCallState|mVoiceRegState|mDataRegState|mPreciseCallState" | head -n 5 | while IFS= read -r l; do
                echo "        $l"
            done
        else
            echo "      [!] Device $dev offline or unreachable via ADB."
        fi
    done
else
    echo "      [!] adb command not installed on host."
fi

echo ""
echo "=============================================================================="
echo " Diagnostic Inspection Completed."
echo "=============================================================================="
