#!/usr/bin/env python3
"""
Automated Call Diagnostic Runner
Coordinates live call attempts, monitors telephony states, and automatically
dumps container logs, XFRM states, and SIP traces upon failure.
Reference: Section III-E (COTS UE Activation and Automated Test Harness)
"""

import os
import sys
import time
import subprocess
from datetime import datetime

TARGET_NUMBER = os.environ.get("CALLEE_NUM", "1002")
TEST_ITERATIONS = int(os.environ.get("TEST_ITERATIONS", "5"))
ADB_DEVICE = os.environ.get("ADB_DEV1", "")

def get_devices():
    global ADB_DEVICE
    if not ADB_DEVICE:
        try:
            out = subprocess.check_output("adb devices", shell=True, text=True)
            devs = [l.split()[0] for l in out.strip().splitlines()[1:] if "\tdevice" in l]
            if devs:
                ADB_DEVICE = devs[0]
            else:
                ADB_DEVICE = "DEVICE_1_SERIAL"
        except Exception:
            ADB_DEVICE = "DEVICE_1_SERIAL"

def run_adb(cmd):
    try:
        return subprocess.check_output(f"adb -s {ADB_DEVICE} shell {cmd}", shell=True, text=True)
    except Exception as e:
        return ""

def get_call_state():
    out = run_adb("dumpsys telephony.registry | grep mCallState")
    if "mCallState=2" in out:
        return 2  # OFFHOOK / Connected
    elif "mCallState=1" in out:
        return 1  # RINGING
    return 0      # IDLE

def toggle_airplane_mode():
    print("[*] Toggling airplane mode to recover state...")
    run_adb("cmd connectivity airplane-mode enable")
    time.sleep(4)
    run_adb("cmd connectivity airplane-mode disable")
    print("[*] Waiting 15 seconds for LTE and IMS attach...")
    time.sleep(15)

def dump_diagnostics(iteration):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    diag_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "diagnostics"))
    os.makedirs(diag_dir, exist_ok=True)
    prefix = os.path.join(diag_dir, f"fail_iter{iteration}_{ts}")
    print(f"[*] Dumping container and kernel diagnostics to {prefix}...")
    
    for c in ["pcscf", "scscf", "mme"]:
        with open(f"{prefix}_{c}.log", "w") as f:
            subprocess.run(f"docker logs {c} --tail 100", shell=True, stdout=f, stderr=subprocess.STDOUT)
            
    with open(f"{prefix}_xfrm.log", "w") as f:
        subprocess.run("docker exec pcscf ip xfrm state", shell=True, stdout=f, stderr=subprocess.STDOUT)

def run_test():
    get_devices()
    print(f"Starting automated call diagnostics ({TEST_ITERATIONS} iterations, target: {TARGET_NUMBER}, device: {ADB_DEVICE})...")
    consecutive_failures = 0
    
    for i in range(1, TEST_ITERATIONS + 1):
        print(f"\n--- Diagnostic Iteration {i}/{TEST_ITERATIONS} ---")
        
        # 1. Trigger Call
        print(f"[*] Dialing {TARGET_NUMBER}...")
        run_adb(f"am start -a android.intent.action.CALL -d tel:{TARGET_NUMBER}")
        
        # 2. Monitor state for 15 seconds
        success = False
        for t in range(15):
            state = get_call_state()
            if state in (1, 2):
                print(f"[+] Call alerting/connected (mCallState={state}) after {t} seconds!")
                success = True
                break
            time.sleep(1)
            
        if not success:
            print("[-] Call failed to reach alerting/offhook state within 15 seconds.")
            
        # 3. Teardown
        print("[*] Ending call session...")
        run_adb("input keyevent KEYCODE_ENDCALL")
        time.sleep(2)
        
        # 4. Evaluate and capture if needed
        if not success:
            consecutive_failures += 1
            dump_diagnostics(i)
            if consecutive_failures >= 2:
                toggle_airplane_mode()
                consecutive_failures = 0
        else:
            consecutive_failures = 0
            print("[+] Iteration passed.")
            
        time.sleep(3)

if __name__ == "__main__":
    run_test()
