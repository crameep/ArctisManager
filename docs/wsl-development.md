# WSL Development

This project targets Linux desktops. If the checkout is on Windows, WSL is the preferred local development environment for syntax checks, tests, packaging, and eventually PipeWire/PulseAudio integration work.

## Current Workspace Check

From PowerShell:

```powershell
wsl.exe sh -lc "cd /mnt/c/Users/crame/OneDrive/Documents/ArctisManager && python3 --version"
```

This workspace has been checked with Ubuntu WSL and Python 3.12.

## Minimal Syntax Check

This check does not require project dependencies and does not write `__pycache__` files:

```bash
python3 - <<'PY'
from pathlib import Path
import ast

files = list(Path("src").rglob("*.py")) + list(Path("tests").rglob("*.py"))
for path in files:
    ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

print(f"AST syntax ok: {len(files)} files")
PY
```

## Test Environment

Ubuntu WSL may not include `pip`, `pytest`, `pactl`, or PipeWire tools by default. Install the development tools inside WSL before running the full test suite:

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv pulseaudio-utils pipewire-bin
```

Then create an isolated environment:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest
```

## Audio Notes

WSL is useful for Python and packaging checks, but headset, udev, D-Bus session, PipeWire, and USB/HID behavior still need to be tested on a real Linux desktop or a WSL setup with the relevant services and USB forwarding configured.
