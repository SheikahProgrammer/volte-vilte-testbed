#!/bin/bash
# ==============================================================================
# COTS Android UE VoLTE & ViLTE CarrierConfig Override Setup
# Configures connected commercial smartphone with carrier overrides and system properties
# ==============================================================================

set -euo pipefail

DEV="${1:-}"

if [ -z "$DEV" ]; then
    echo "Usage: $0 <ADB_DEVICE_SERIAL>"
    echo "Available ADB devices:"
    adb devices -l
    exit 1
fi

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_XML="$DIR/carrier_config_override.xml"

echo "[*] Configuring COTS Android device: $DEV"

# Verify root access
if ! adb -s "$DEV" shell "su -c 'id'" 2>/dev/null | grep -q "uid=0"; then
    echo "[!] Warning: Device does not appear to have su/root access."
    echo "    Root privileges are required to push CarrierConfig XML overrides directly."
fi

# 1. Enable VoLTE / ViLTE vendor radio properties
echo "[*] Setting vendor telephony system properties..."
adb -s "$DEV" shell "su -c 'setprop persist.vendor.radio.volte_service 1'" 2>/dev/null || true
adb -s "$DEV" shell "su -c 'setprop persist.vendor.radio.vilte_service 1'" 2>/dev/null || true
adb -s "$DEV" shell "su -c 'setprop persist.vendor.radio.enhanced_4g 1'" 2>/dev/null || true
adb -s "$DEV" shell "su -c 'setprop persist.dbg.volte_avail_ovr 1'" 2>/dev/null || true
adb -s "$DEV" shell "su -c 'setprop persist.dbg.vt_avail_ovr 1'" 2>/dev/null || true
adb -s "$DEV" shell "su -c 'setprop persist.dbg.wfc_avail_ovr 0'" 2>/dev/null || true

# 2. Deploy CarrierConfig XML override to Phone app data storage
echo "[*] Pushing CarrierConfig override XML..."
TARGET_DIR="/data/user_de/0/com.android.phone/files"
adb -s "$DEV" push "$CONFIG_XML" /data/local/tmp/carrier_config_override.xml
adb -s "$DEV" shell "su -c 'mkdir -p $TARGET_DIR && cp /data/local/tmp/carrier_config_override.xml $TARGET_DIR/carrier_config_carrierid_1_testbed.xml && chown -R radio:radio $TARGET_DIR && chmod 660 $TARGET_DIR/*.xml'"
adb -s "$DEV" shell "rm /data/local/tmp/carrier_config_override.xml"

# 3. Reload carrier config via airplane mode toggle
echo "[*] Toggling airplane mode to reload telephony configuration..."
adb -s "$DEV" shell cmd connectivity airplane-mode enable
sleep 3
adb -s "$DEV" shell cmd connectivity airplane-mode disable
sleep 5

echo "[✓] COTS UE setup completed successfully for $DEV."
