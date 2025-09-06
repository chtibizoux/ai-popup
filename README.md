# AI Popup

Small Qt app to send selected/clipboard text to a local LLM (Ollama) with a quick instruction.

## Wayland clipboard support

On Wayland, Qt clipboard access can be unreliable. This app will use `wl-clipboard` tools if available:

- Reads with `wl-paste` (tries primary selection first, then clipboard)
- Writes with `wl-copy`

If `wl-clipboard` is not installed, it falls back to the standard Qt clipboard API.

Install on most distros:

- Arch: `pacman -S wl-clipboard`
- Debian/Ubuntu: `apt install wl-clipboard`
- Fedora: `dnf install wl-clipboard`

## Requirements

- Python 3
- PySide6
- requests
- Ollama running locally (`ollama serve` etc.)

## Run

```
python3 src/main.py
```
