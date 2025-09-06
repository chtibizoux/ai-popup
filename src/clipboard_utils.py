import shutil
import subprocess
from PySide6.QtGui import QGuiApplication, QClipboard


def _has_cmd(name: str) -> bool:
    return shutil.which(name) is not None


def _wl_paste(primary: bool = True, timeout_ms: int = 700) -> str | None:
    if not _has_cmd("wl-paste"):
        return None
    try:
        args = ["wl-paste", "-n"]
        if primary:
            args.append("-p")
        out = subprocess.check_output(
            args,
            timeout=timeout_ms / 1000.0,
        )
        return out.decode("utf-8", errors="replace")
    except Exception:
        return None


def _wl_copy(text: str) -> bool:
    if not _has_cmd("wl-copy"):
        return False
    try:
        proc = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE)
        proc.communicate(input=text.encode("utf-8"), timeout=1.0)
        return proc.returncode == 0
    except Exception:
        return False


def read_text() -> str:
    """
    Read text from Wayland primary/clipboard if possible, else Qt clipboard.
    Returns an empty string if nothing is found.
    """
    text = _wl_paste(primary=True) or _wl_paste(primary=False)
    if text is None or not text.strip():
        cb = QGuiApplication.clipboard()
        text = cb.text(QClipboard.Mode.Selection)
        if not text:
            text = cb.text()
    return text or ""


def write_text(text: str) -> None:
    """Write to Wayland via wl-copy if available; otherwise use Qt clipboard."""
    if not _wl_copy(text):
        cb = QGuiApplication.clipboard()
        cb.setText(text)
