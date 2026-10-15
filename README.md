# Private 4G VoLTE & ViLTE Cellular Testbed

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![3GPP](https://img.shields.io/badge/3GPP-Release_15-green.svg)](https://www.3gpp.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![srsRAN](https://img.shields.io/badge/srsRAN_4G-23.10-orange.svg)](https://github.com/srsran/srsRAN_4G)
[![Open5GS](https://img.shields.io/badge/Open5GS-v2.7.6-blue.svg)](https://open5gs.org/)
[![Kamailio](https://img.shields.io/badge/Kamailio-v5.7.0-red.svg)](https://www.kamailio.org/)

An end-to-end, reproducible empirical blueprint for deploying a private 4G LTE/IMS cellular network providing native Voice over LTE (VoLTE) and Video over LTE (ViLTE) using commercial off-the-shelf (COTS) Android smartphones over Software-Defined Radio (SDR) hardware.

---

## Architecture Overview

The testbed coordinates four primary tiers across hardware, radio access, and containerized core network services:

```
[ COTS UE 1 (Infinix X668) ]       [ COTS UE 2 (Itel A60) ]
              \                         /
         Over-the-Air RF (Band 3 FDD, 3 MHz BW, EARFCN 1300)
                          |
             [ Ettus USRP B200 SDR Transceiver ]
                          | (USB 3.0 / UHD)
           [ srsRAN 4G eNodeB (Linux Host) ]
                          |
   S1-MME (SCTP: 36412)   |   S1-U (GTP-U: 2152)
                          v
================ Docker Bridge Network (172.22.0.0/24) ================
|                                                                     |
|  [ EPC Tier - Open5GS ]                                             |
|  • MME (172.22.0.9)     • SGW-C/U (172.22.0.5/.6)                   |
|  • SMF (172.22.0.7)     • UPF (172.22.0.8, ogstun / ogstun2)        |
|  • HSS (172.22.0.3)     • PCRF (172.22.0.4, static PCC rules)       |
|                                                                     |
|  [ IMS Tier - Kamailio & RTPEngine ]                                |
|  • P-CSCF (172.22.0.21, IPsec ESP SAs, Gm interface)               |
|  • I-CSCF (172.22.0.19) • S-CSCF (172.22.0.20)                      |
|  • RTPEngine (172.22.0.16, dynamic media proxy)                     |
|  • SMSC (172.22.0.33, SMS-over-IP)                                  |
|                                                                     |
|  [ Authentication & Database Tier ]                                 |
|  • PyHSS (172.22.0.18, Diameter Cx/Sh)                              |
|  • MySQL (172.22.0.17, ims_hss_db)                                  |
|  • MongoDB (172.22.0.2, open5gs core db)                            |
|                                                                     |
|  [ Infrastructure & Telemetry Tier ]                                |
|  • DNS (172.22.0.15, BIND9)                                         |
|  • Prometheus (172.22.0.36) • Grafana (172.22.0.39)                 |
|  • OsmoMSC / OsmoHLR (172.22.0.31/.32, CSFB fallback)               |
=======================================================================
```

---

## Repository Structure

```
.
├── core_network/                      # 22-Container Core Network & IMS Deployment
│   ├── docker-compose.yaml            # Multi-tier Docker Compose manifest
│   ├── .env.example                   # Network and IP configuration template
│   ├── pcscf/                         # P-CSCF config with automated XFRM flush hook
│   ├── icscf/                         # I-CSCF routing and Cx diameter config
│   ├── scscf/                         # S-CSCF session management
│   ├── pcrf/                          # Policy and Charging Rules Function config
│   ├── pyhss/                         # PyHSS Diameter Cx/Sh authentication daemon
│   ├── mysql/                         # MySQL database initialization for IMS
│   └── open5gs/                       # Open5GS EPC configuration files (MME, UPF, SMF)
│
├── ran_config/                        # srsRAN 4G (Release 23.10) eNodeB Configuration
│   ├── enb.conf                       # RF front-end parameters (Band 3, 15 PRBs)
│   ├── rb.conf                        # Radio bearer profile with status_report_required=true
│   ├── rr.conf                        # Cell and radio resource parameters
│   └── sib.conf                       # SIB scheduling configuration
│
├── cots_ue/                           # COTS Handset Provisioning & Carrier Overrides
│   ├── carrier_config_override.xml    # CarrierConfig XML toggles for VoLTE/ViLTE
│   └── setup_cots_ue.sh               # ADB provisioning script for rooted Android UEs
│
├── provisioning/                      # Dual-Database Synchronization & SIM Programming
│   ├── sample_subscribers.json        # Sanitized Open5GS subscriber MongoDB entries
│   ├── patch_qci2_pcc.py              # Script injecting static QCI 2 video PCC rules
│   ├── init_pyhss_db.sql              # MySQL initialization for PyHSS subscriber records
│   └── program_sim.sh                 # pySim-prog programming template for USIMs
│
└── test_harness/                      # Automated Verification & Latency Benchmarking
    ├── benchmark_calls.sh             # 9-step automated functional stability harness (sweeps of call cycles)
    ├── diagnostic_utility.sh          # Forensic analyzer for SIP, ESP counts, XFRM, logcat
    ├── diagnose_calls.py              # Automated call diagnostics & recovery runner
    └── generate_plots.py              # Protocol milestone latency breakdown plot generator
```

---

## Prerequisites

### 1. Hardware Requirements
* **SDR Front-End**: Ettus USRP B200 / B210 (USB 3.0 interface).
* **RF Attenuation / Enclosure**: RF-shielded box or direct coax cabling with $\ge 30\text{ dB}$ attenuation.
* **Commercial Handsets**: 2x COTS Android smartphones (e.g., Unisoc T616 / SC9863A1 or equivalent rooted devices).
* **SIM Cards**: Programmable USIM cards (e.g., Sysmocom `sysmoUSIM-SJS1`) and a USB PC/SC smart card reader.

### 2. Software Requirements
* **Operating System**: Linux (Ubuntu 22.04 LTS / Debian 12 recommended).
* **Docker Engine** ($\ge 24.0$) and **Docker Compose Plugin** ($\ge 2.20$).
* **UHD** ($\ge 4.4.0$) and **srsRAN 4G** (Release 23.10).
* **Python 3** ($\ge 3.8$) with `matplotlib`, `numpy`, and `pySim`.
* **Android Debug Bridge (`adb`)**.

---

## Step-by-Step Reproduction Guide

### Step 1: USIM Programming
Program two SysmoUSIM-SJS1 cards with standard 3GPP test credentials matching PLMN `001-01`:
```bash
cd provisioning/
./program_sim.sh 0 001010000000001 <ADM_KEY_CARD_1>
./program_sim.sh 0 001010000000002 <ADM_KEY_CARD_2>
```

### Step 2: COTS UE Telephony Configuration
Connect each Android smartphone via USB and execute the carrier override script:
```bash
cd ../cots_ue/
./setup_cots_ue.sh <DEVICE_1_ADB_SERIAL>
./setup_cots_ue.sh <DEVICE_2_ADB_SERIAL>
```

### Step 3: Dual-Database Provisioning
1. **Initialize Open5GS MongoDB Subscribers**:
   ```bash
   python3 provisioning/patch_qci2_pcc.py provisioning/sample_subscribers.json
   # Import into MongoDB once core network is running:
   # docker exec -i mongo mongoimport --db open5gs --collection subscribers --file - < provisioning/sample_subscribers.json
   ```
2. **Initialize PyHSS MySQL Database**:
   ```bash
   # Import subscriber authentication vectors into MySQL:
   # docker exec -i mysql mysql -u root -pims ims_hss_db < provisioning/init_pyhss_db.sql
   ```

### Step 4: Launch Core Network
```bash
cd ../core_network/
cp .env.example .env
docker compose up -d
```
Verify that MME S1AP interface is listening:
```bash
docker logs -f mme | grep "s1ap_server"
```

### Step 5: Start srsRAN eNodeB
On the Linux host:
```bash
cd ../ran_config/
sudo srsenb enb.conf
```
Confirm the COTS handsets attach and establish default bearer (QCI 9) and IMS signaling bearer (QCI 5).

### Step 6: Automated Functional Stability & State Verification
The multi-cycle test harness coordinates handset device control, state machine validation, and failure analysis across repeated call cycles:

1. **Run Multi-Cycle Verification Sweeps (e.g., 10 Sweeps of 5 Call Cycles)**:
```bash
cd ../test_harness/
ADB_DEV1=<SERIAL_PHONE1> ADB_DEV2=<SERIAL_PHONE2> ./benchmark_calls.sh 10 5
```
Each iteration executes the full 9-step verification cycle:
- `[1/9]` Synchronous airplane mode reset (4s toggle)
- `[2/9]` LTE attach verification via telephony registry polling
- `[3/9]` 25-second IMS PhoneCallTracker & IPsec stabilization
- `[4/9]` P-CSCF location table query (`ulpcscf.status`) & callee IP resolution
- `[5/9]` Kernel IPsec SA verification (`ip xfrm state`)
- `[6/9]` Outgoing call initiation via ADB keycodes, ringing detection, answer, 5s media hold
- `[7/9]` In-dialog ViLTE video upgrade via dialer keyevent & secondary QCI 2 bearer verification
- `[8/9]` Call teardown
- `[9/9]` Automatic diagnostic snapshot capture on failure

2. **Dedicated Sustained Call Evaluation (5-minute continuous call)**:
```bash
./benchmark_calls.sh 1 1 --sustained-5min
```

3. **Run Forensic Diagnostic Utility**:
Inspect control-plane SIP signaling milestones, IPsec ESP tunnel packet counts, kernel XFRM policies/SAs, CSCF logs, and Android logcat:
```bash
./diagnostic_utility.sh
# Or dissect a captured PCAP trace:
./diagnostic_utility.sh --pcap /path/to/trace.pcap
```

> **Note on Measurements:** `benchmark_calls.sh` validates end-to-end device operational stability across physical handsets. Microsecond-level control-plane protocol milestones (e.g., SIP INVITE $\rightarrow$ 180 Ringing, RRC Connection Request $\rightarrow$ Setup) are extracted directly from network packet captures and eNodeB execution traces via the diagnostic utility.

### Step 7: Plot Protocol Breakdown Chart
Generate the control-plane protocol latency breakdown chart (`fig_kpi_breakdown.pdf`):
```bash
python3 generate_plots.py
```

---

## Empirical Troubleshooting Matrix

| Challenge | Root Cause Protocol Mechanism | Applied Operational Resolution |
| :--- | :--- | :--- |
| **Radio Bearer (QCI 5 Drops)** | Missing `statusReportRequired = true` in `PDCP-Config` for RLC-AM bearers (3GPP TS 36.323 cl. 5.4.1). | Explicitly configured `status_report_required = true` in `ran_config/rb.conf`. |
| **Signaling Authorization** | Container bridge NAT causes SDP media IP vs. Gx framed IP mismatch during Diameter Rx session gating. | Disabled dynamic Rx (`##!define WITH_RX` in `pcscf.cfg`); pre-provisioned static PCC rules in PCRF. |
| **IPsec State Exhaustion** | Rapid handset reconnection leaves stale kernel XFRM states on Gm endpoint, triggering `duplicate SPI` errors. | Integrated automated XFRM flush hook in Kamailio `route[REGISTER]`. |
| **Gateway Session Abort** | Dynamic TFT deletion (`0b101` per TS 24.301) triggers assertion lookup fault in gateway during video downgrade. | Pre-provisioned QCI 2 static PCC rule; deferred bearer teardown to SIP `BYE`. |

---

## License

This project is licensed under the [Apache License 2.0](LICENSE).
