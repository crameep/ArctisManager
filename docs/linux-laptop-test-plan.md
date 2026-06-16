# Linux Laptop Test Plan

Use this checklist when testing the redesigned GUI on a real Linux laptop with an Arctis headset or dongle attached. WSL is useful for development checks, but USB/HID, udev, D-Bus, systemd user services, and PipeWire/PulseAudio routing need a real Linux session.

## 1. Install System Packages

Debian or Ubuntu:

```bash
sudo apt update
sudo apt install -y git python3 python3-pip python3-venv pipx libpulse0 libxcb-cursor0
```

Fedora:

```bash
sudo dnf install -y git python3 python3-pip pipx pulseaudio-libs xcb-util-cursor
```

Arch:

```bash
sudo pacman -S --needed git python python-pipx libpulse xcb-util-cursor
```

## 2. Install This Branch

```bash
git clone --branch codex/start-from-linux-arctis-manager https://github.com/crameep/ArctisManager.git
cd ArctisManager
python3 -m pipx ensurepath
python3 -m pipx install --force .
```

If `lam-gui` is not found immediately after install, open a new terminal or run it as `~/.local/bin/lam-gui`.

## 3. Smoke Test Without Hardware

```bash
lam-gui --demo
```

Check that the app opens to the redesigned dark dashboard and that these pages are visible:

- Dashboard
- Mixer
- Device
- Routing
- Profiles
- Settings

## 4. Hardware Setup

Plug in the Arctis headset, DAC, or wireless dongle, then run:

```bash
lam-cli tools arctis-devices
lam-cli setup --start-now
systemctl --user status arctis-manager --no-pager
```

If the service is active, launch the real GUI:

```bash
lam-gui
```

## 5. What To Verify

- Dashboard shows the connected headset or DAC status.
- Battery, mic mute, and other supported status fields update when the hardware reports them.
- Mixer shows Game, Chat, Media, Aux, and planned Microphone rows.
- ChatMix balance is readable and changes when the hardware reports new values.
- Routing shows virtual endpoint readiness.
- Profiles can save a named profile and load it again.
- Settings shows setup and service state clearly.

Do not treat Microphone routing, EQ, noise suppression, app auto-switching, or PipeWire-native routing as complete yet. Those are planned or future areas unless the GUI says otherwise.

## 6. Collect Debug Info

If something fails, collect:

```bash
lam-cli tools arctis-devices
pactl list short sinks
pactl list short sink-inputs
systemctl --user status arctis-manager --no-pager
journalctl --user -u arctis-manager -n 200 --no-pager
```

Also note the Linux distribution, desktop environment, headset model, and whether the headset is connected by USB cable, DAC, or wireless dongle.

## 7. Cleanup

```bash
systemctl --user disable --now arctis-manager
python3 -m pipx uninstall linux-arctis-manager
rm -rf ~/.config/arctis_manager
```
