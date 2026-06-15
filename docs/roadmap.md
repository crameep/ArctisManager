# Roadmap

## Current Baseline

The project already has a Python daemon, D-Bus service, PySide GUI, CLI setup tools, udev rule generation, per-device YAML configurations, profile persistence, and virtual audio output sinks through PulseAudio compatibility.

The first routing expansion adds a Sonar-style endpoint catalog for Game, Chat, Media, Aux, and a planned Microphone source. Game, Chat, Media, and Aux are implemented as virtual output sinks. Microphone is intentionally marked as planned until a safe source implementation exists.

The first UI expansion adds a dashboard-first PySide shell with mixer, routing, device, profiles, and settings pages. It is inspired by modern audio control workflows, but uses original layout, naming, and iconography and remains clearly unaffiliated with SteelSeries.

## MVP

- Keep the app building and testable without attached hardware.
- List headset USB/HID details through `lam-cli tools arctis-devices`.
- Detect supported devices from YAML configuration.
- Read status for supported models.
- Persist general and per-device settings.
- Create virtual Game, Chat, Media, and Aux output sinks.
- Apply ChatMix to Chat separately from Game, Media, and Aux.
- Keep the GUI driven by D-Bus settings/status metadata.

## Beta

- Add native PipeWire/WirePlumber backend support.
- Expose audio endpoint state over D-Bus.
- Add per-app routing commands and GUI controls.
- Add route persistence by application identity.
- Add stronger mock coverage for PulseAudio/PipeWire and USB flows.
- Replace any non-original branding assets with project-owned artwork.

## Advanced

- Virtual microphone source.
- Parametric EQ and EQ preset management.
- Noise suppression, compressor, limiter, and mic monitoring experiments.
- Profile switching by app/game.
- Firmware-aware capability detection.
- Plugin or extension points for model-specific controls.

## Definition Of Done For The First Milestone

- Application entry points are present: daemon, CLI, and GUI.
- CLI can inspect SteelSeries USB/HID headset candidates.
- Daemon architecture exists and is D-Bus-backed.
- Virtual Game, Chat, Media, and Aux outputs are implemented or safely stubbed.
- Profile storage works through XDG-style config paths.
- Docs describe implemented, planned, and hardware-testing-needed areas.
