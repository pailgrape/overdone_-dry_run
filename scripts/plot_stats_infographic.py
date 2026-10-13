#!/usr/bin/env python3
"""
Create a compact infographic PNG summarizing the Analysis_Complete.md data.

Output: stats_infographic.png

Requirements:
  pip install numpy matplotlib seaborn

Run:
  python scripts/plot_stats_infographic.py

Note: This file was added to the repository to generate a compact infographic with
all key numbers, CI bands, token frequencies, and short notes.
"""

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Data extracted from Analysis_Complete.md
mean = 133.00
std = 189.59
median = 20.00
ci_low = np.array([414.3, 377.4, -6.4, -17.6, -36.6, -35.9, -22.5])
ci_high = np.array([484.9, 451.5, 69.7, 57.6, 36.4, 40.2, 51.9])
success_prob = 87.0  # percent

top_tokens = [
    ("then", 36), ("sudo", 22), ("null", 21), ("run_net", 20),
    ("true", 18), ("install", 17), ("local", 15), ("ntsync", 13),
    ("return", 12), ("echo", 11)
]

table1_actions = [
    ("akmods --force + reboot", "NVIDIA driver", "No (already working)"),
    ("usermod -a -G render,video", "AMD ROCm access", "Yes, if you want to use ROCm"),
    ("dnf install rocm", "Full ROCm stack", "Optional")
]

rocm_notes = [
    "HIP_VISIBLE_DEVICES=0 rocminfo  # if the app is using system ROCm",
    "sudo usermod -a -G render,video $USER",
    "sudo dnf install rocm"
]

nvidia_note = "After the RPM Fusion akmod-nvidia-580xx packages were installed, the proprietary driver took over."

# Styling
sns.set(style='white')
palette = sns.color_palette('muted')

fig = plt.figure(figsize=(9, 12), constrained_layout=True)
# layout: top title, then a grid with left charts (2 rows) and right text panels
gs = fig.add_gridspec(6, 4)

# Title
ax_title = fig.add_subplot(gs[0, :])
ax_title.axis('off')
ax_title.text(0.5, 0.5, 'Analysis Summary — Compact Infographic', ha='center', va='center',
              fontsize=18, fontweight='bold')

# Left top: summary numeric (mean/std/median) + mean CI
ax_stats = fig.add_subplot(gs[1:3, 0:2])
ax_stats.set_title('Key Statistics', fontsize=12)
ax_stats.axis('off')

# Big numbers
ax_stats.text(0.02, 0.75, f'Mean: {mean:.2f}', fontsize=14, weight='bold')
ax_stats.text(0.02, 0.62, f'Std : {std:.2f}', fontsize=12)
ax_stats.text(0.02, 0.50, f'Median: {median:.2f}', fontsize=12)

# mean +/- std bar
ax_stats.barh([0], [mean], xerr=[std], color=palette[0], alpha=0.8, height=0.35)
ax_stats.set_xlim(0, max(mean + std, np.max(ci_high)) * 1.1)
ax_stats.text(mean + std * 0.02, -0.05, 'mean ± std', fontsize=9)

# mean +/- 95% CI (normal approx)
z = 1.96
mean_ci_low = mean - z * std
mean_ci_high = mean + z * std
ax_stats.hlines([-0.6], mean_ci_low, mean_ci_high, colors=palette[2], linewidth=4)
ax_stats.text(mean_ci_high + 5, -0.6, 'mean ± 95% CI', fontsize=9, color=palette[2])

# Overlay median marker
ax_stats.scatter([median], [-0.2], color=palette[1], s=80, label='median')
ax_stats.text(median + 5, -0.25, 'median', color=palette[1], fontsize=9)

# Left middle: CI band small plot
ax_ci = fig.add_subplot(gs[3, 0:2])
x = np.arange(len(ci_low))
ax_ci.fill_between(x, ci_low, ci_high, color=palette[3], alpha=0.3)
ax_ci.plot(x, ci_low, linestyle='--', marker='o', color='gray', markersize=4)
ax_ci.plot(x, ci_high, linestyle='--', marker='o', color='gray', markersize=4)
ax_ci.axhline(mean, color=palette[0], linestyle='-', label=f'mean={mean:.0f}')
ax_ci.axhline(median, color=palette[1], linestyle='--', label=f'median={median:.0f}')
ax_ci.set_title('7-element 95% CI ranges', fontsize=11)
ax_ci.set_xlabel('Index')
ax_ci.set_ylabel('Value')
ax_ci.legend(fontsize=8)

# Left bottom: token frequency bar chart
ax_tokens = fig.add_subplot(gs[4:6, 0:2])
labels = [t[0] for t in top_tokens][::-1]
counts = [t[1] for t in top_tokens][::-1]
ax_tokens.barh(labels, counts, color=palette[1])
ax_tokens.set_title('Top token frequencies', fontsize=11)
ax_tokens.set_xlabel('Count')

# Right column top: success probability gauge-like indicator and summary text
ax_right_top = fig.add_subplot(gs[1:3, 2:4])
ax_right_top.axis('off')
ax_right_top.text(0, 0.9, 'Dry-run success probability', fontsize=12, weight='bold')
# Draw a simple horizontal gauge
gauge_x = np.linspace(0, 1, 200)
ax_right_top.fill_between(gauge_x, 0.2, 0.6, color='#e6e6e6')
ax_right_top.fill_between(gauge_x[gauge_x <= success_prob / 100.0], 0.2, 0.6, color=palette[0])
ax_right_top.text(0.5, 0.35, f'{success_prob:.1f}%', ha='center', va='center', fontsize=20, weight='bold')

# Add short summary bullets
summary_lines = [
    'Script lines: 449 (non-empty 415)',
    'Functions defined: 20',
    'dnf install mentions: 13',
    'Dry-run mode: no packages would be installed'
]
for i, line in enumerate(summary_lines):
    ax_right_top.text(0, 0.05 + i * 0.08, f'• {line}', fontsize=9)

# Right middle: table1 actions
ax_right_mid = fig.add_subplot(gs[3, 2:4])
ax_right_mid.axis('off')
ax_right_mid.text(0, 0.95, 'Key actions (NVIDIA / ROCm)', fontsize=12, weight='bold')
for i, (cmd, purpose, note) in enumerate(table1_actions):
    y = 0.75 - i * 0.25
    ax_right_mid.text(0, y, f'- {cmd}  |  {purpose}  |  {note}', fontsize=9)

# Right bottom: notes block
ax_right_bot = fig.add_subplot(gs[4:6, 2:4])
ax_right_bot.axis('off')
ax_right_bot.text(0, 0.95, 'ROCm notes', fontsize=11, weight='bold')
for i, ln in enumerate(rocm_notes):
    ax_right_bot.text(0, 0.75 - i * 0.12, f'• {ln}', fontsize=9)

ax_right_bot.text(0, 0.25, 'NVIDIA note', fontsize=11, weight='bold')
ax_right_bot.text(0, 0.12, nvidia_note, fontsize=9)

# Footer: small provenance
ax_footer = fig.add_subplot(gs[5, :])
ax_footer.axis('off')
ax_footer.text(0.01, 0.1, 'Source: Analysis_Complete.md (commit 4c3e62f)', fontsize=7, color='gray')

out = 'stats_infographic.png'
plt.savefig(out, dpi=200, bbox_inches='tight')
print(f'Saved {out}')
