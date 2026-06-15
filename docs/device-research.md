# Device Research

This project uses device YAML files as the source of truth for supported Arctis models. The bundled configurations currently include:

- `arctis_7_plus.yaml`
- `nova_5.yaml`
- `nova_7_wireless_discrete_battery.yaml`
- `nova_7_wireless_perc_battery.yaml`
- `nova_elite.yaml`
- `nova_pro_wireless.yaml`
- `nova_pro_wired.yaml`

The existing research captures USB vendor/product IDs, HID command interfaces, listen interfaces, status request packets, response mappings, status parsers, and setting update sequences. See `docs/device_support.md` and `docs/device_configuration_file_specs.md` for the workflow and schema.

## Known Capability Areas

- Device detection by SteelSeries vendor ID and known product IDs.
- USB/HID command writes and status reads.
- Battery and online state for supported models.
- ChatMix where the device exposes `media_mix` and `chat_mix`.
- Device-specific settings such as sidetone, mic volume, ANC, transparency, gain, Bluetooth, power management, and wireless mode where mapped.
- PulseAudio/PipeWire-compatible virtual output sinks.

## Unknown Or Incomplete Areas

- Native PipeWire/WirePlumber endpoint creation and routing.
- Per-application routing UI and persistence.
- Virtual microphone source behavior.
- Firmware version discovery.
- EQ preset and parametric EQ behavior across models.
- Complete capability detection for unsupported product IDs.
- Legal review of any asset or branding that is not original to this project.

## Research Rules

- Prefer user-submitted USB descriptors, `lam-cli tools arctis-devices`, and documented packet observations.
- Keep unsupported features marked as unknown or not implemented.
- Avoid copying proprietary UI, branding, firmware, assets, or undocumented code.
- Keep new device behavior in YAML whenever possible, with code changes only for new parser/control primitives.
