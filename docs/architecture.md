# Architecture

Linux Arctis Manager is a Python application with three user-facing entry points:

- `lam-daemon`: the long-running device and audio service.
- `lam-cli`: setup and hardware-research utilities.
- `lam-gui`: the PySide desktop UI and tray app.

The project is based on `elegos/Linux-Arctis-Manager` and is licensed under GPL-3.0. This codebase should remain careful about compatibility language: SteelSeries, Arctis, Sonar, and GG are referenced only to describe supported hardware and interoperability goals.

## Runtime Layers

`CoreEngine` in `src/linux_arctis_manager/core.py` owns the daemon workflow. It loads device YAML files, monitors USB devices, initializes supported headsets, reads status packets, writes setting commands, updates profile files, and coordinates virtual audio endpoints.

`USBDevicesMonitor` watches for SteelSeries USB devices via `pyudev`. Hardware-specific behavior is configured in YAML files under `src/linux_arctis_manager/devices` and optionally under `~/.config/arctis_manager/devices`.

`PulseAudioManager` in `src/linux_arctis_manager/pactl.py` manages audio endpoints through the PulseAudio API. On modern Linux this normally talks to PipeWire through `pipewire-pulse`. Native PipeWire/WirePlumber control is not implemented yet.

`DbusManager` exposes daemon state and settings over D-Bus so the GUI, tray app, CLI, and external integrations can consume the same service.

## Audio Routing

Virtual audio endpoint definitions live in `src/linux_arctis_manager/audio_endpoints.py`. The implemented output endpoints are:

- `Arctis_Game`
- `Arctis_Chat`
- `Arctis_Media`
- `Arctis_Aux`

The planned input endpoint is:

- `Arctis_Microphone`

Only output sinks are currently implemented. Each output sink is created as a null sink and looped back to the physical headset sink. ChatMix is modeled as two mix groups: `chat` applies to `Arctis_Chat`, while `media` applies to `Arctis_Game`, `Arctis_Media`, and `Arctis_Aux`.

The D-Bus settings service exposes the virtual endpoint catalog and current PulseAudio/PipeWire-pulse state. GUI clients can show whether each implemented virtual output is present, missing, or the current default output without talking to PulseAudio directly.

## Configuration And Profiles

Device capabilities are data-driven. YAML files define vendor/product IDs, USB command/listen interfaces, init packets, status parsers, setting controls, and UI grouping.

Per-device settings are stored in `~/.config/arctis_manager/settings/<vendor>_<product>.yaml`. General settings are stored in `~/.config/arctis_manager/settings/general_settings.yaml`.

Named per-device profiles are stored separately in `~/.config/arctis_manager/profiles/<vendor>_<product>.yaml`. A profile is a snapshot of the current device setting values. The D-Bus settings service exposes profile metadata and save/load methods so GUI clients can manage profiles without knowing the file format.

## GUI And CLI

The GUI reads D-Bus settings, status, profile metadata, and audio endpoint state dynamically instead of hardcoding device-specific controls. The Profiles page uses the settings service to save and load named snapshots for the connected device. The Routing page uses the same service to show virtual output readiness and to refresh endpoint state on demand. The CLI currently focuses on setup tasks, udev generation, desktop entries, and USB/HID discovery.

## Testing Strategy

Hardware-dependent behavior should stay behind mockable interfaces. Existing tests cover status parsing, config parsing, CLI USB formatting helpers, daemon single-instance behavior, and the virtual endpoint catalog. CI should not require a physical headset.

## Open Architecture Work

- Add a native PipeWire/WirePlumber backend alongside the PulseAudio compatibility backend.
- Add per-app routing inspection and reassignment.
- Implement a virtual microphone source.
- Keep USB packet handling data-driven and avoid risky reverse-engineering practices.
