# Fedora 44 KDE Gaming — Maintenance, Diagnostics & Launch Options

Practical post-setup workflow for the Fedora 44 KDE Plasma gaming system analyzed in this repository (`master/original_setup.sh`).

These steps keep the system updated, resolve common NVIDIA package conflicts, capture hardware profiles, and provide ready-to-use Steam launch options.

## 1. System & Application Updates

### Native packages (DNF)
```bash
sudo dnf upgrade --refresh
```

### Flatpaks (Discover backend)
```bash
flatpak update
```

### Clean unused dependencies
```bash
sudo dnf autoremove
flatpak uninstall --unused
```

## 2. Resolving NVIDIA Package Conflicts

### Symptom
During `dnf upgrade` you may see an RPM transaction failure similar to:
```
Transaction failed: Rpm transaction failed.
  - file /usr/lib64/libnvidia-ml.so.1 from install of nvidia-driver-common-3:620.70.06-1.fc44.x86_64
    conflicts with file from package xorg-x11-drv-nvidia-580xx-cuda-libs-3:580.196.07-1.fc44.x86_64
  - file /usr/lib64/libnvidia-cfg.so.1 from install of nvidia-driver-common-3:620.70.06-1.fc44.x86_64
    conflicts with file from package xorg-x11-drv-nvidia-580xx-libs-3:580.196.07-1.fc44.x86_64
```

This occurs when legacy `nvidia-580xx` packages remain while newer NVIDIA driver packages are pulled in.

### Resolution
```bash
sudo dnf remove "*nvidia-580xx*"
sudo dnf clean all
sudo dnf upgrade --refresh
sudo reboot
```

After reboot, verify with `nvidia-smi` (if the proprietary driver is in use) or by checking that the modules load cleanly.

## 3. Verification Checkpoints

- **DNF upgrade**: ends with `Complete!`. Confirm with `sudo dnf needs-restarting -r`.
- **Flatpak**: `flatpak update` reports `Nothing to do.` or lists successful updates.
- **NVIDIA**: no lingering version mismatches; `nvidia-smi` (if applicable) or module status is clean.
- **NTSYNC / GameMode**: `/dev/ntsync` exists and `systemctl --user is-active gamemoded.service` is active (as set up by the original script).

## 4. Optimized Steam Launch Options

Right-click the game in Steam → **Properties** → **General** → paste into **Launch Options**.

### Full Stack (Gamescope + FSR Upscaling + MangoHud + GameMode)
```bash
gamemoderun gamescope -W 1920 -H 1080 -w 1280 -h 720 -r 60 -F fsr --mangoapp -- %command%
```

| Flag | Purpose |
|------|---------|
| `gamemoderun` | Applies GameMode performance profile (CPU prioritization, renice, etc. on the Ryzen 9 5950X). |
| `-W 1920 -H 1080` | Output display resolution (match your monitor). |
| `-w 1280 -h 720` | Internal rendering resolution (lower for higher frame rates). |
| `-r 60` | Nested output refresh rate (change to 120/144/etc. as needed). |
| `-F fsr` | Gamescope built-in AMD FSR spatial upscaler. |
| `--mangoapp` | Injects MangoHud overlay into the Gamescope loop. |
| `--` | Separates Gamescope args from the game command. |

Adjust resolutions to your display and performance target. For native 1080p rendering, drop or match the `-w`/`-h` values.

### Native Display Mode (No Gamescope)
```bash
gamemoderun mangohud %command%
```

## 5. Hardware Diagnostic Tool

A standalone interactive HTML tool is available at [`docs/hardware-diagnostic-tool.html`](hardware-diagnostic-tool.html).

Open it in a browser, copy the diagnostic commands, run them in Konsole, and paste the output to generate a Markdown summary suitable for GitHub issues or troubleshooting notes.

## Notes

- These procedures are complementary to the statistical analysis of `master/original_setup.sh`.
- The original script installs the RPM Fusion NVIDIA akmod stack, GameMode, MangoHud, Gamescope, and the Plasma Gamescope launcher (`~/.local/bin/plasma-gamescope-steam`).
- Always back up or note your current driver packages before removing `*nvidia-580xx*` packages.
