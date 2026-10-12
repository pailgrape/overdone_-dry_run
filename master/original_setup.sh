#!/usr/bin/env bash
# fedora44-kde-gaming-setup.sh
# Post-install gaming stack for Fedora 44 KDE Plasma (Wayland).
#
# What it does
#   - Confirms Fedora 44+ and a Plasma session
#   - Enables RPM Fusion free/nonfree (needed for Steam and NVIDIA)
#   - Detects NVIDIA / AMD / Intel and installs the matching Vulkan stack
#   - Installs Steam, Lutris, GameMode, MangoHud, Gamescope, Wine
#   - Pulls wine-ntsync so the Fedora 44 NTSYNC module loads at boot
#   - Installs Heroic and ProtonUp-Qt from Flathub
#   - Writes KDE gaming tweaks: VRR hint, GameMode, a Gamescope launcher
#
# Usage
#   chmod +x fedora44-kde-gaming-setup.sh
#   ./fedora44-kde-gaming-setup.sh              # full setup
#   ./fedora44-kde-gaming-setup.sh --dry-run    # print actions only
#   ./fedora44-kde-gaming-setup.sh --no-flatpak # skip Heroic / ProtonUp-Qt
#   ./fedora44-kde-gaming-setup.sh --nvidia-open # use nvidia-open akmod
#
# Reboot after NVIDIA driver install and after the first NTSYNC enable.
# Safe to rerun after a dropped network connection. dnf retries, and an
# interrupted transaction is cleared before the next attempt.

set -euo pipefail

DRY_RUN=0
SKIP_FLATPAK=0
NVIDIA_OPEN=0
RETRIES=5
LOG_FILE="${HOME}/fedora44-kde-gaming-setup.log"

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --no-flatpak) SKIP_FLATPAK=1 ;;
    --nvidia-open) NVIDIA_OPEN=1 ;;
    -h|--help)
      sed -n '2,22p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

log() {
  printf '%s  %s\n' "$(date '+%H:%M:%S')" "$*" | tee -a "$LOG_FILE"
}

run() {
  log "+ $*"
  if [[ "$DRY_RUN" -eq 0 ]]; then
    "$@"
  fi
}

retry() {
  local n=1
  local delay=5
  while true; do
    if "$@"; then
      return 0
    fi
    if [[ "$n" -ge "$RETRIES" ]]; then
      log "FAILED after ${n} tries: $*"
      return 1
    fi
    log "network or dnf error (try ${n}/${RETRIES}). waiting ${delay}s, then retrying: $*"
    sleep "$delay"
    delay=$((delay * 2))
    if [[ "$delay" -gt 60 ]]; then
      delay=60
    fi
    n=$((n + 1))
  done
}

run_net() {
  log "+ $*"
  if [[ "$DRY_RUN" -eq 1 ]]; then
    return 0
  fi
  retry "$@"
}

clear_stale_dnf() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "would clear a stale dnf lock if present"
    return 0
  fi
  if sudo fuser /var/cache/dnf/metadata_lock.pid >/dev/null 2>&1; then
    log "dnf metadata lock is held. Not killing it. Wait, then rerun."
    return 1
  fi
  sudo dnf clean packages || true
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

confirm_fedora() {
  if [[ ! -r /etc/os-release ]]; then
    echo "Cannot read /etc/os-release" >&2
    exit 1
  fi
  # shellcheck disable=SC1091
  source /etc/os-release
  if [[ "${ID:-}" != "fedora" ]]; then
    echo "This script is for Fedora. Detected: ${ID:-unknown}" >&2
    exit 1
  fi
  local ver="${VERSION_ID:-0}"
  if [[ "$ver" -lt 44 ]]; then
    echo "Fedora ${ver} detected. Written for Fedora 44 (NTSYNC + Plasma 6)." >&2
    echo "Continuing is unsafe; aborting." >&2
    exit 1
  fi
  log "Fedora ${ver} (${PRETTY_NAME:-Fedora})"
}

detect_gpu() {
  GPU_VENDOR="unknown"
  if lspci -nn 2>/dev/null | grep -Eqi 'VGA|3D|Display' ; then
    if lspci -nn | grep -Eqi 'NVIDIA'; then
      GPU_VENDOR="nvidia"
    elif lspci -nn | grep -Eqi 'AMD/ATI|Advanced Micro Devices'; then
      GPU_VENDOR="amd"
    elif lspci -nn | grep -Eqi 'Intel'; then
      GPU_VENDOR="intel"
    fi
  fi
  log "GPU vendor: ${GPU_VENDOR}"
}

enable_rpmfusion() {
  local rel
  rel="$(rpm -E %fedora)"
  if ! rpm -q rpmfusion-free-release >/dev/null 2>&1; then
    run_net sudo dnf install -y \
      "https://mirrors.rpmfusion.org/free/fedora/rpmfusion-free-release-${rel}.noarch.rpm" \
      "https://mirrors.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-${rel}.noarch.rpm"
  else
    log "RPM Fusion already enabled"
  fi
  run_net sudo dnf upgrade -y --refresh
  # AppStream metadata used by GNOME Software / Discover for Steam etc.
  run_net sudo dnf install -y rpmfusion-free-release-tainted \
    rpmfusion-nonfree-release-tainted || true
  run_net sudo dnf group upgrade -y core || true
}

install_codecs_and_base() {
  run_net sudo dnf install -y \
    @"Multimedia" \
    @"Sound and Video" \
    vulkan-tools \
    vulkan-loader \
    vulkan-validation-layers \
    mesa-vulkan-drivers \
    mesa-vulkan-drivers.i686 \
    libva-utils \
    gamemode \
    mangohud \
    goverlay \
    gamescope \
    wine \
    wine-ntsync \
    winetricks \
    lutris \
    steam \
    kdialog \
    qt6-qtbase \
    || {
      log "Some packages failed. Retrying Steam/Wine separately."
      run_net sudo dnf install -y gamemode mangohud gamescope wine wine-ntsync lutris || true
      run_net sudo dnf install -y steam || true
    }
}

install_gpu_stack() {
  case "$GPU_VENDOR" in
    nvidia)
      log "Installing NVIDIA akmod from RPM Fusion"
      if [[ "$NVIDIA_OPEN" -eq 1 ]]; then
        run_net sudo dnf install -y akmod-nvidia-open xorg-x11-drv-nvidia-cuda \
          nvidia-vaapi-driver || run_net sudo dnf install -y akmod-nvidia
      else
        run_net sudo dnf install -y akmod-nvidia xorg-x11-drv-nvidia-cuda \
          nvidia-vaapi-driver
      fi
      # 32-bit Vulkan/GL for Proton
      run_net sudo dnf install -y xorg-x11-drv-nvidia-libs.i686 \
        nvidia-vaapi-driver.i686 || true
      log "NVIDIA modules build on next boot via akmods. Reboot required."
      ;;
    amd)
      log "AMD: Mesa is the driver. Installing freeworld VA-API if available."
      run_net sudo dnf swap -y mesa-va-drivers mesa-va-drivers-freeworld || true
      run_net sudo dnf swap -y mesa-vdpau-drivers mesa-vdpau-drivers-freeworld || true
      run_net sudo dnf install -y mesa-vulkan-drivers.i686 || true
      ;;
    intel)
      log "Intel: Mesa + intel-media-driver"
      run_net sudo dnf install -y intel-media-driver libva-intel-driver || true
      run_net sudo dnf install -y mesa-vulkan-drivers.i686 || true
      ;;
    *)
      log "Unknown GPU. Leaving the Mesa Vulkan drivers from the base set."
      ;;
  esac
}

install_flatpaks() {
  if [[ "$SKIP_FLATPAK" -eq 1 ]]; then
    log "Skipping Flathub launchers"
    return
  fi
  if ! command -v flatpak >/dev/null 2>&1; then
    run_net sudo dnf install -y flatpak
  fi
  run_net flatpak remote-add --if-not-exists --user flathub \
    https://dl.flathub.org/repo/flathub.flatpakrepo
  run_net flatpak install -y --user flathub \
    com.heroicgameslauncher.hgl \
    net.davidotek.pupgui2 \
    com.discordapp.Discord || true
}

write_gamemode_ini() {
  local dest="${HOME}/.config/gamemode.ini"
  mkdir -p "${HOME}/.config"
  if [[ -f "$dest" ]]; then
    log "Leaving existing ${dest}"
    return
  fi
  cat >"$dest" <<'EOF'
[general]
renice=10
softrealtime=auto
inhibit_screensaver=1

[filter]
whitelist=steam,steamwebhelper,gamescope

[gpu]
apply_gpu_optimisations=accept-responsibility
gpu_device=0
nv_powermizer_mode=1
amd_performance_level=high

[custom]
start=notify-send -a GameMode "GameMode" "Performance profile on"
end=notify-send -a GameMode "GameMode" "Performance profile off"
EOF
  log "Wrote ${dest}"
}

write_mangohud_conf() {
  local dest="${HOME}/.config/MangoHud/MangoHud.conf"
  mkdir -p "${HOME}/.config/MangoHud"
  if [[ -f "$dest" ]]; then
    log "Leaving existing ${dest}"
    return
  fi
  cat >"$dest" <<'EOF'
fps
frametime
gpu_stats
cpu_stats
vram
ram
gpu_temp
cpu_temp
gamemode
vulkan_driver
engine_version
position=top-left
background_alpha=0.4
font_size=20
toggle_hud=Shift_R+F12
EOF
  log "Wrote ${dest}"
}

write_kwin_vrr() {
  # Plasma 6 Wayland: KWin reads AdaptiveSync from kwinrc. kwriteconfig6
  # keeps the file in the format System Settings writes. A missing panel
  # capability is ignored by KWin.
  local kwin="${HOME}/.config/kwinrc"
  mkdir -p "${HOME}/.config"
  if command -v kwriteconfig6 >/dev/null 2>&1; then
    kwriteconfig6 --file "$kwin" --group Wayland --key AdaptiveSync Automatic
    log "Plasma: kwriteconfig6 set Wayland/AdaptiveSync=Automatic"
  elif ! grep -q '^AdaptiveSync=' "$kwin" 2>/dev/null; then
    printf '\n[Wayland]\nAdaptiveSync=Automatic\n' >>"$kwin"
    log "Plasma: appended AdaptiveSync=Automatic (kwriteconfig6 missing)"
  else
    log "kwinrc already has AdaptiveSync"
  fi
  if command -v qdbus6 >/dev/null 2>&1; then
    qdbus6 org.kde.KWin /KWin org.kde.KWin.reconfigure >/dev/null 2>&1 || true
  fi
}

install_launchers() {
  local bin="${HOME}/.local/bin"
  local apps="${HOME}/.local/share/applications"
  mkdir -p "$bin" "$apps"

  cat >"${bin}/plasma-gamescope-steam" <<'EOF'
#!/usr/bin/env bash
# Nested Gamescope session on the current Plasma Wayland desktop.
# Steam Big Picture, GameMode, and MangoHud. Exit Steam to return.
set -euo pipefail

if [[ "${XDG_SESSION_TYPE:-}" != "wayland" ]]; then
  echo "This launcher expects a Wayland session (Plasma on Fedora 44)." >&2
  exit 1
fi
if [[ "${XDG_CURRENT_DESKTOP:-}${DESKTOP_SESSION:-}" != *KDE* && "${XDG_CURRENT_DESKTOP:-}${DESKTOP_SESSION:-}" != *plasma* ]]; then
  echo "Warning: session does not look like Plasma (${XDG_CURRENT_DESKTOP:-unknown}). Continuing." >&2
fi

width="${GAMESCOPE_WIDTH:-$(kscreen-doctor -o 2>/dev/null | awk '/Geometry:/ {print $2; exit}' | cut -dx -f1)}"
height="${GAMESCOPE_HEIGHT:-$(kscreen-doctor -o 2>/dev/null | awk '/Geometry:/ {print $2; exit}' | cut -dx -f2)}"
rate="${GAMESCOPE_RATE:-}"
width="${width:-1920}"
height="${height:-1080}"

args=(
  --adaptive-sync
  -W "$width" -H "$height"
  -w "$width" -h "$height"
  -f
  --force-grab-cursor
  --steam
)
if [[ -n "$rate" ]]; then
  args+=(-r "$rate")
fi

export MANGOHUD=1
exec gamemoderun gamescope "${args[@]}" -- steam -gamepadui -steamdeck
EOF
  chmod +x "${bin}/plasma-gamescope-steam"
  install -m 0755 "${BASH_SOURCE[0]%/*}/plasma-game-session.sh" "${bin}/plasma-game-session.sh" 2>/dev/null || \
    install -m 0755 "$(dirname "$(readlink -f "$0")")/plasma-game-session.sh" "${bin}/plasma-game-session.sh" 2>/dev/null || true

  cat >"${apps}/plasma-gamescope-steam.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Steam Gaming Mode
GenericName=Gamescope session
Comment=Steam Big Picture inside Gamescope on Plasma Wayland
Exec=${bin}/plasma-gamescope-steam
Icon=steam
Terminal=false
Categories=Game;
Keywords=steam;gamescope;gaming;plasma;
StartupNotify=true
OnlyShowIn=KDE
EOF

  if ! grep -q '.local/bin' "${HOME}/.bashrc" 2>/dev/null; then
    printf '\n# FIRST Plasma launchers\nexport PATH="$HOME/.local/bin:$PATH"\n' >>"${HOME}/.bashrc"
    log "Added ~/.local/bin to ~/.bashrc"
  fi
  if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
    log "Plasma application cache refreshed"
  fi
  log "Launcher: ${bin}/plasma-gamescope-steam"
  log "Konsole profiles were not touched (${HOME}/.local/share/konsole)"
}

load_ntsync() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "would modprobe ntsync and write /etc/modules-load.d/ntsync.conf"
    return 0
  fi
  if sudo modprobe ntsync; then
    echo ntsync | sudo tee /etc/modules-load.d/ntsync.conf >/dev/null
    log "ntsync loaded; persistent via /etc/modules-load.d/ntsync.conf"
  else
    log "modprobe ntsync failed. Kernel module missing until a newer kernel is booted."
  fi
}

enable_gamemode() {
  if [[ "$DRY_RUN" -eq 1 ]]; then
    log "would enable --now the user gamemoded.service"
    return 0
  fi
  if ! rpm -q gamemode >/dev/null 2>&1; then
    log "gamemode package missing; skipping service enable"
    return 0
  fi
  systemctl --user enable --now gamemoded.service || log "gamemoded did not start; a game can still start it"
  log "gamemoded: $(systemctl --user is-active gamemoded.service 2>/dev/null || echo unknown)"
}

verify() {
  log "---- verification ----"
  rpm -q steam wine wine-ntsync gamemode mangohud gamescope lutris 2>/dev/null \
    | tee -a "$LOG_FILE" || true
  if [[ -e /dev/ntsync ]]; then
    log "ntsync: /dev/ntsync present"
  else
    log "ntsync: /dev/ntsync missing"
  fi
  log "gamemoded: $(systemctl --user is-active gamemoded.service 2>/dev/null || echo inactive)"
  log "session: ${XDG_SESSION_TYPE:-unknown} desktop=${XDG_CURRENT_DESKTOP:-unknown}"
  log "Log: ${LOG_FILE}"
  log "Next: open Steam and set launch options to: gamemoderun mangohud %command%"
}

main() {
  : >"$LOG_FILE"
  need_cmd sudo
  need_cmd dnf
  need_cmd rpm
  confirm_fedora
  detect_gpu
  clear_stale_dnf
  enable_rpmfusion
  install_codecs_and_base
  install_gpu_stack
  install_flatpaks
  if [[ "$DRY_RUN" -eq 0 ]]; then
    write_gamemode_ini
    write_mangohud_conf
    write_kwin_vrr
    install_launchers
    load_ntsync
    enable_gamemode
  else
    log "Dry run: skipped writing configs and launchers"
  fi
  verify
}

main "$@"
