=== overdone_-dry_run Statistical Analysis ===
Script lines: 449 (non-empty 415)
Comments: 32
Functions defined: 20 → ['log', 'run', 'retry', 'run_net', 'clear_stale_dnf', 'need_cmd', 'confirm_fedora', 'detect_gpu', 'enable_rpmfusion', 'install_codecs_and_base', 'install_gpu_stack', 'install_flatpaks', 'write_gamemode_ini', 'write_mangohud_conf', 'write_kwin_vrr', 'install_launchers', 'load_ntsync', 'enable_gamemode', 'verify', 'main']
run() calls: 1, run_net() (retry): 1
dnf install mentions: 13

PyTorch tensor stats on counts:
  mean=133.00  std=189.59  median=20.00
  95% CI low:  [414.3, 377.4, -6.4, -17.6, -36.6, -35.9, -22.5]
  95% CI high: [484.9, 451.5, 69.7, 57.6, 36.4, 40.2, 51.9]

Simulated dry-run success probability: 87.0%
(higher because of built-in retry logic on network/dnf calls)

Top token frequencies (rough package/command proxy):
  then: 36
  sudo: 22
  null: 21
  run_net: 20
  true: 18
  install: 17
  local: 15
  ntsync: 13
  return: 12
  echo: 11

Dry-run mode: no packages would be installed; only logged actions.
Original script supports --dry-run, --no-flatpak, --nvidia-open.

=== table1.csv actions (NVIDIA / ROCm) ===
  - akmods --force + reboot | NVIDIA driver | No (already working)
  - usermod -a -G render,video | AMD ROCm access | Yes, if you want to use ROCm
  - dnf install rocm | Full ROCm stack | Optional

=== ROCm notes for AMD Radeon VII ===
HIP_VISIBLE_DEVICES=0 rocminfo   # if the app is using system ROCm
sudo usermod -a -G render,video $USER
sudo dnf install rocm

=== NVIDIA note ===
After the RPM Fusion akmod-nvidia-580xx packages were installed, the proprietary driver took over.

[dry-run] Analysis complete. No side effects.
