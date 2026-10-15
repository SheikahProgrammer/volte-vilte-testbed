#!/usr/bin/env python3
"""
patch_qci2_pcc.py
Ensures that Open5GS MongoDB subscriber document has static PCC rules provisioned
for dedicated conversational video bearer (QCI 2) under the IMS APN session.
Reference: Section IV-D and Section III-D of the paper.
"""

import sys
import json
from pathlib import Path

def patch_subscriber_data(input_file, output_file=None):
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"[ERROR] Input file {input_path} not found.")
        sys.exit(1)

    with open(input_path, 'r') as f:
        data = json.load(f)

    modified_count = 0
    for sub in data:
        for slice_obj in sub.get('slice', []):
            for session in slice_obj.get('session', []):
                if session.get('name') == 'ims':
                    pcc_rules = session.get('pcc_rule', [])
                    has_qci2 = any(rule.get('qos', {}).get('index') == 2 for rule in pcc_rules)
                    if not has_qci2:
                        qci2_rule = {
                            "qos": {
                                "arp": {
                                    "priority_level": 2,
                                    "pre_emption_capability": 1,
                                    "pre_emption_vulnerability": 1
                                },
                                "mbr": {
                                    "downlink": {"value": 500, "unit": 2},
                                    "uplink": {"value": 500, "unit": 2}
                                },
                                "gbr": {
                                    "downlink": {"value": 200, "unit": 2},
                                    "uplink": {"value": 200, "unit": 2}
                                },
                                "index": 2
                            },
                            "flow": []
                        }
                        pcc_rules.append(qci2_rule)
                        modified_count += 1

    out_path = Path(output_file) if output_file else input_path
    with open(out_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"[✓] Patched {modified_count} subscriber IMS session(s) with QCI 2 static PCC rules in {out_path}.")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 patch_qci2_pcc.py <subscribers.json> [output.json]")
        sys.exit(1)
    in_f = sys.argv[1]
    out_f = sys.argv[2] if len(sys.argv) > 2 else None
    patch_subscriber_data(in_f, out_f)
