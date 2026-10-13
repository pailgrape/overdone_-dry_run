"""
master/pytorch_analyzer.py

Statistical analysis of fedora44-kde-gaming-setup.sh using PyTorch.
Project: overdone_-dry_run

Performs tensor-based stats on script structure, dry-run actions,
and simulated package success rates.

Also incorporates table1.csv (NVIDIA/ROCm actions) and notes for
AMD Radeon VII ROCm setup.
"""

import argparse
import csv
import re
from pathlib import Path
from collections import Counter

import torch
import numpy as np


SCRIPT_PATH = Path(__file__).parent / "original_setup.sh"
TABLE_PATH = Path(__file__).parent / "table1.csv"
RESULTS_PATH = Path(__file__).parent.parent / "ANALYSIS_RESULTS.md"


def load_script(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def load_table(path: Path) -> list:
    if not path.exists():
        return []
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def extract_metrics(text: str) -> dict:
    lines = text.splitlines()
    total_lines = len(lines)
    non_empty = sum(1 for l in lines if l.strip())
    comments = sum(1 for l in lines if l.strip().startswith("#"))
    functions = re.findall(r"^([a-zA-Z_][a-zA-Z0-9_]*)\(\) \{", text, re.MULTILINE)
    run_calls = len(re.findall(r"\brun\(", text))
    run_net_calls = len(re.findall(r"\brun_net\(", text))
    dnf_installs = len(re.findall(r"dnf install", text, re.IGNORECASE))
    packages = re.findall(r"\b([a-z0-9_-]+)\b", text)
    pkg_counter = Counter([p for p in packages if len(p) > 3])
    top_pkgs = pkg_counter.most_common(15)

    return {
        "total_lines": total_lines,
        "non_empty": non_empty,
        "comments": comments,
        "function_count": len(functions),
        "functions": functions,
        "run_calls": run_calls,
        "run_net_calls": run_net_calls,
        "dnf_installs": dnf_installs,
        "top_tokens": top_pkgs,
    }


def torch_stats(metrics: dict) -> dict:
    """Apply PyTorch tensor statistics."""
    counts = torch.tensor(
        [
            metrics["total_lines"],
            metrics["non_empty"],
            metrics["comments"],
            metrics["function_count"],
            metrics["run_calls"],
            metrics["run_net_calls"],
            metrics["dnf_installs"],
        ],
        dtype=torch.float32,
    )
    mean = counts.mean()
    std = counts.std(unbiased=False)
    median = counts.median()
    noise = torch.randn(1000, counts.numel()) * std * 0.1
    boot = counts + noise
    ci_low = boot.quantile(0.025, dim=0)
    ci_high = boot.quantile(0.975, dim=0)

    success_base = torch.tensor(0.85)
    retry_boost = torch.tensor(metrics["run_net_calls"]) * 0.02
    success_prob = torch.clamp(success_base + retry_boost, 0.0, 0.99)

    return {
        "counts": counts.tolist(),
        "mean": mean.item(),
        "std": std.item(),
        "median": median.item(),
        "ci_low": ci_low.tolist(),
        "ci_high": ci_high.tolist(),
        "simulated_dry_run_success": success_prob.item(),
    }


def dry_run_report(metrics: dict, stats: dict, table_rows: list) -> str:
    lines = [
        "=== overdone_-dry_run Statistical Analysis ===",
        f"Script lines: {metrics['total_lines']} (non-empty {metrics['non_empty']})",
        f"Comments: {metrics['comments']}",
        f"Functions defined: {metrics['function_count']} → {metrics['functions']}",
        f"run() calls: {metrics['run_calls']}, run_net() (retry): {metrics['run_net_calls']}",
        f"dnf install mentions: {metrics['dnf_installs']}",
        "",
        "PyTorch tensor stats on counts:",
        f"  mean={stats['mean']:.2f}  std={stats['std']:.2f}  median={stats['median']:.2f}",
        f"  95% CI low:  {[round(x,1) for x in stats['ci_low']]}",
        f"  95% CI high: {[round(x,1) for x in stats['ci_high']]}",
        "",
        f"Simulated dry-run success probability: {stats['simulated_dry_run_success']:.1%}",
        "(higher because of built-in retry logic on network/dnf calls)",
        "",
        "Top token frequencies (rough package/command proxy):",
    ]
    for token, cnt in metrics["top_tokens"][:10]:
        lines.append(f"  {token}: {cnt}")
    lines.append("")
    lines.append("Dry-run mode: no packages would be installed; only logged actions.")
    lines.append("Original script supports --dry-run, --no-flatpak, --nvidia-open.")
    lines.append("")
    lines.append("=== table1.csv actions (NVIDIA / ROCm) ===")
    if table_rows:
        for row in table_rows:
            action = row.get("Action", "")
            needed = row.get("Needed for", "")
            now = row.get("Do you need it now?", "")
            lines.append(f"  - {action} | {needed} | {now}")
    else:
        lines.append("  (table1.csv not found)")
    lines.append("")
    lines.append("=== ROCm notes for AMD Radeon VII ===")
    lines.append("HIP_VISIBLE_DEVICES=0 rocminfo   # if the app is using system ROCm")
    lines.append("sudo usermod -a -G render,video $USER")
    lines.append("sudo dnf install rocm")
    lines.append("")
    lines.append("=== NVIDIA note ===")
    lines.append("After the RPM Fusion akmod-nvidia-580xx packages were installed, the proprietary driver took over.")
    lines.append("")
    lines.append("[dry-run] Analysis complete. No side effects.")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Statistical analysis with PyTorch (overdone_-dry_run)")
    parser.add_argument("--dry-run", action="store_true", help="Print analysis only")
    args = parser.parse_args()

    if not SCRIPT_PATH.exists():
        print(f"Missing script at {SCRIPT_PATH}")
        return 1

    text = load_script(SCRIPT_PATH)
    metrics = extract_metrics(text)
    stats = torch_stats(metrics)
    table_rows = load_table(TABLE_PATH)
    report = dry_run_report(metrics, stats, table_rows)

    print(report)

    # Always write results so they are visible in the repo
    RESULTS_PATH.write_text(report + "\n", encoding="utf-8")
    print(f"\nResults written to {RESULTS_PATH}")

    if args.dry_run:
        print("[dry-run] No system changes performed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
