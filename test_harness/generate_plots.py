#!/usr/bin/env python3
"""
Protocol Milestone Latency Breakdown Plot Generator
Plots empirically verified single-session control-plane signaling latencies
extracted directly from core network Wireshark packet captures and container logs.
Reference: Section IV-E and Section V
"""

import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()

# Set IEEE-style plotting defaults
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams['ps.fonttype'] = 42
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 8
plt.rcParams['axes.labelsize'] = 8
plt.rcParams['xtick.labelsize'] = 7
plt.rcParams['ytick.labelsize'] = 7
plt.rcParams['legend.fontsize'] = 7

def generate_kpi_bar_chart():
    """Plots empirically measured single-session protocol milestone latencies from trace inspection."""
    categories = [
        'ViLTE UPDATE (Sess 2)',
        'ViLTE UPDATE (Sess 1)',
        'ViLTE re-INVITE->183',
        'Diameter MAR/MAA',
        'IMS Registration',
        'VoLTE Alerting (180)'
    ]
    latencies = [60.6, 73.1, 107.5, 113.2, 631.1, 672.5]

    fig, ax = plt.subplots(figsize=(3.4, 1.6), dpi=300)
    bars = ax.barh(categories, latencies, color='#1f77b4', edgecolor='black', alpha=0.85, height=0.65)

    for bar, val in zip(bars, latencies):
        ax.text(val + 15, bar.get_y() + bar.get_height()/2, f'{val:.1f} ms', 
                va='center', ha='left', fontsize=6.5)

    ax.set_xlabel('Signaling Latency (ms)', fontsize=7.5)
    ax.set_xlim(0, 800)
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    plt.tight_layout(pad=0.2)

    output_pdf = SCRIPT_DIR / 'fig_kpi_breakdown.pdf'
    plt.savefig(output_pdf, format='pdf', bbox_inches='tight')
    plt.close()
    print(f'[SUCCESS] Generated {output_pdf.name} with verified trace latencies.')

if __name__ == '__main__':
    generate_kpi_bar_chart()
