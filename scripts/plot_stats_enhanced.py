#!/usr/bin/env python3
"""
Enhanced plotting script for the stats from Analysis_Complete.md

This script produces a PNG with three panels:
 - Left: bar showing mean ± std and mean ± 95% CI (scalar)
 - Middle: the 7-element 95% CI arrays plotted as a band with mean & median
 - Right: histogram + KDE of simulated data consistent with the given mean/median/std

Requirements:
  pip install numpy matplotlib seaborn scipy

Run:
  python scripts/plot_stats_enhanced.py

Output:
  stats_plot_enhanced.png

Notes:
 - I cannot run this script in this environment; run it locally or in CI to produce the PNG.
"""

import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import lognorm

# Given scalars
mean = 133.00
std = 189.59
median = 20.00

# Provided 7-element 95% CI arrays
ci_low = np.array([414.3, 377.4, -6.4, -17.6, -36.6, -35.9, -22.5])
ci_high = np.array([484.9, 451.5, 69.7, 57.6, 36.4, 40.2, 51.9])

# Compute a single-scalar 95% CI around the mean (normal-approx)
z = 1.96
mean_ci_low = mean - z * std
mean_ci_high = mean + z * std

# Seed for reproducibility
rng = np.random.default_rng(12345)

# Simulate data consistent with mean/median using a lognormal parametrization.
# For a lognormal variable: median = exp(mu), mean = exp(mu + sigma^2/2)
# Solve for mu = ln(median), sigma^2 = 2*(ln(mean) - mu)
# If the equation gives sigma^2 <= 0 (numerical issues), fall back to using std in normal.
mu = math.log(max(median, 1e-9))
try:
    sigma2 = 2.0 * (math.log(max(mean, 1e-9)) - mu)
    if sigma2 <= 0 or not math.isfinite(sigma2):
        raise ValueError("non-positive sigma2")
    sigma = math.sqrt(sigma2)
    # Draw samples from lognormal with these parameters
    sim_samples = rng.lognormal(mean=mu, sigma=sigma, size=20000)
except Exception:
    # Fallback: draw from a normal truncated at zero
    sim_samples = rng.normal(loc=mean, scale=std, size=20000)
    sim_samples = sim_samples[sim_samples > 0]

# Setup seaborn style
sns.set(style='whitegrid')
palette = sns.color_palette('tab10')

fig, axs = plt.subplots(1, 3, figsize=(18, 5))

# Panel 1: Summary bar with mean ± std and mean ± 95% CI
ax = axs[0]
ax.bar(0, mean, yerr=std, capsize=12, color=palette[0], alpha=0.85, label='mean ± std')
# Draw mean ± 95% CI as a thicker errorbar (in a different color)
ax.errorbar(0.0, mean, yerr=np.array([[mean - mean_ci_low], [mean_ci_high - mean]]).reshape(2,1),
            fmt='o', color=palette[2], capsize=8, markersize=6, label='mean ± 95% CI')
ax.scatter(0, median, color=palette[1], zorder=5, s=80, label=f'median = {median:.2f}')
ax.set_xlim(-1, 1)
ax.set_xticks([0])
ax.set_xticklabels(['counts'])
ax.set_ylabel('Value')
ax.set_title('Summary: mean ± std and mean ± 95% CI')
ax.legend()
ax.annotate(f'mean={mean:.2f}', xy=(0, mean), xytext=(0.1, mean + 0.05 * std),
            arrowprops=dict(arrowstyle='->', color=palette[0]), color=palette[0])
ax.annotate(f'median={median:.2f}', xy=(0, median), xytext=(0.1, median + 0.05 * std),
            arrowprops=dict(arrowstyle='->', color=palette[1]), color=palette[1])

# Panel 2: 7-element CI arrays with band and mean/median lines
ax = axs[1]
x = np.arange(len(ci_low))
# Plot low/high as lines
ax.plot(x, ci_low, linestyle='--', marker='o', color='gray', label='95% CI low')
ax.plot(x, ci_high, linestyle='--', marker='o', color='gray', label='95% CI high')
ax.fill_between(x, ci_low, ci_high, color=palette[2], alpha=0.2, label='95% CI band')
# Overlay mean and median
ax.axhline(mean, color=palette[0], linestyle='-', linewidth=2, label=f'mean = {mean:.2f}')
ax.axhline(median, color=palette[1], linestyle='-', linewidth=2, label=f'median = {median:.2f}')
ax.set_xticks(x)
ax.set_xlabel('Index')
ax.set_ylabel('Value')
ax.set_title('95% CI arrays (low vs high) with mean & median')
ax.legend(loc='best')

# Panel 3: Histogram + KDE of simulated data
ax = axs[2]
# histogram
sns.histplot(sim_samples, bins=80, kde=True, color=palette[3], stat='density', ax=ax, edgecolor='none', alpha=0.6)
# mark mean & median
sample_mean = np.mean(sim_samples)
sample_median = np.median(sim_samples)
ax.axvline(sample_mean, color=palette[0], linestyle='-', linewidth=2, label=f'sim mean = {sample_mean:.2f}')
ax.axvline(sample_median, color=palette[1], linestyle='--', linewidth=2, label=f'sim median = {sample_median:.2f}')
# mark mean ± std and mean ± 95% CI
ax.axvline(mean - std, color=palette[4], linestyle=':', linewidth=1, label='mean - std')
ax.axvline(mean + std, color=palette[4], linestyle=':', linewidth=1, label='mean + std')
ax.axvline(mean_ci_low, color=palette[2], linestyle='-.', linewidth=1.5, label='mean - 1.96*std')
ax.axvline(mean_ci_high, color=palette[2], linestyle='-.', linewidth=1.5, label='mean + 1.96*std')
ax.set_xlabel('Simulated counts')
ax.set_ylabel('Density')
ax.set_title('Histogram + KDE of simulated data (lognormal fit via median)')
ax.legend(loc='upper right')

plt.tight_layout()
outname = 'stats_plot_enhanced.png'
plt.savefig(outname, dpi=200)
print(f'Saved {outname}')
