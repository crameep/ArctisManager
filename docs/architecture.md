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

Only output sinks are currently implemented. Each output sink is created as a null sink and looped back to the physical headset sink. ChatMix is modeled as two mix groups: `chat` applies to `Arctis_Chat`, while `media` applies to `Arctis_Game`, `Arctis_Media`, and `Arctis_Aux`. The Mixer page displays channel readiness, mix-group membership, and reported mix groups as read-only meters so users can see the current hardware balance without implying software-side ChatMix control that is not implemented yet.

The D-Bus settings service exposes the virtual endpoint catalog and current PulseAudio/PipeWire-pulse state. GUI clients can show whether each implemented virtual output is present, missing, or the current default output without talking to PulseAudio directly.

The same service lists active application playback streams and can move a stream to an implemented virtual output by sink-input index. This is a direct PulseAudio/PipeWire-pulse reassignment for currently active streams. Persistent per-app policy still belongs to future native PipeWire/WirePlumber work.

## Configuration And Profiles

Device capabilities are data-driven. YAML files define vendor/product IDs, USB command/listen interfaces, init packets, status parsers, setting controls, and UI grouping.

Per-device settings are stored in `~/.config/arctis_manager/settings/<vendor>_<product>.yaml`. General settings are stored in `~/.config/arctis_manager/settings/general_settings.yaml`.

Named per-device profiles are stored separately in `~/.config/arctis_manager/profiles/<vendor>_<product>.yaml`. A profile is a snapshot of the current device setting values. The D-Bus settings service exposes profile metadata and save/load methods so GUI clients can manage profiles without knowing the file format.

## GUI And CLI

The GUI reads D-Bus settings, status, profile metadata, audio endpoint state, and active application routes dynamically instead of hardcoding device-specific controls. The Dashboard summarizes headset health, ChatMix, active app routes, and exposed control areas so the first screen behaves like a compact control surface. The Device page groups exposed headset controls into capability areas such as microphone, noise control, power/wireless, and DAC/display behavior so unsupported features stay visible as unavailable rather than being implied to work. The Profiles page uses the settings service to save and load named snapshots for the connected device, summarize saved profile metadata, and show app/game profile automation as planned. The Routing page uses the same service to summarize ready virtual outputs and active app streams, show detailed virtual output readiness, refresh endpoint state on demand, and move active app streams to ready virtual outputs. The Settings page includes service state and setup guidance for D-Bus, udev rules, the current PulseAudio/PipeWire-pulse backend, and optional tray autostart. The CLI currently focuses on setup tasks, udev generation, desktop entries, and USB/HID discovery.

## Testing Strategy

Hardware-dependent behavior should stay behind mockable interfaces. Existing tests cover status parsing, config parsing, CLI USB formatting helpers, daemon single-instance behavior, and the virtual endpoint catalog. CI should not require a physical headset.

## Open Architecture Work

- Add a native PipeWire/WirePlumber backend alongside the PulseAudio compatibility backend.
- Add persistent per-app routing by application identity.
- Implement a virtual microphone source.
- Keep USB packet handling data-driven and avoid risky reverse-engineering practices.
