# Optimized Steam Launch Options

Right-click your game in Steam → **Properties** → **General** → paste one of the following into the **Launch Options** field.

These are tailored for the Fedora 44 KDE Plasma gaming setup (Ryzen 9 5950X + AMD/NVIDIA GPU) analyzed in this repository.

## 1. Full Stack (Gamescope + FSR Upscaling + MangoHud + GameMode)

Recommended for most titles when you want a nested Gamescope session with upscaling and overlays.

```bash
gamemoderun gamescope -W 1920 -H 1080 -w 1280 -h 720 -r 60 -F fsr --mangoapp -- %command%
```

### What these flags do

| Flag | Purpose |
|------|---------|
| `gamemoderun` | Applies GameMode CPU/GPU performance profile (prioritizes the game on the Ryzen 9 5950X scheduler, raises process priority, etc.). |
| `-W 1920 -H 1080` | Output / display resolution (match your monitor; 1080p in this example). |
| `-w 1280 -h 720` | Internal rendering resolution. Lower than output (720p here) to raise frame rates. |
| `-r 60` | Refresh rate of the nested Gamescope output. Change to `120`, `144`, or your monitor’s rate. |
| `-F fsr` | Enables Gamescope’s built-in AMD FidelityFX Super Resolution spatial upscaler (scales the lower internal resolution up to the output resolution). |
| `--mangoapp` | Injects the MangoHud overlay directly into the Gamescope compositor loop. |
| `--` | Separates Gamescope arguments from the game command (`%command%`). |

Adjust `-W`/`-H` and `-w`/`-h` to your display and performance target. For native 1080p rendering drop the lower `-w`/`-h` pair (or set them equal to output).

## 2. Native Display Mode (No Gamescope)

Runs the game on the desktop compositor with only GameMode + MangoHud.

```bash
gamemoderun mangohud %command%
```

Use this when you prefer the game to use the full desktop resolution and refresh rate without a nested compositor.

## Notes

- The setup script analyzed in this repo (`master/original_setup.sh`) already installs GameMode, MangoHud, and Gamescope and creates a Plasma Gamescope launcher.
- These launch options are per-game overrides you paste in Steam.
- For NVIDIA systems you may also want `PROTON_ENABLE_NVAPI=1` or other Proton flags depending on the title (check ProtonDB).
- Always test without Gamescope first if a game has issues starting or with input.

Related: see the original Plasma Gamescope launcher written by the setup script under `~/.local/bin/plasma-gamescope-steam`.
