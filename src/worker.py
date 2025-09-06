import json
import requests
from PySide6.QtCore import QObject, Signal
from constants import OLLAMA_URL


class StreamWorker(QObject):
    chunk = Signal(str)
    done = Signal()
    error = Signal(str)

    def __init__(self, model: str, prompt: str, parent=None):
        super().__init__(parent)
        self.model = model
        self.prompt = prompt
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        payload = {
            "model": self.model,
            "prompt": self.prompt,
            "stream": True,
        }
        try:
            with requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60) as resp:
                resp.raise_for_status()
                for line in resp.iter_lines():
                    if self._stop:
                        break
                    if not line:
                        continue
                    try:
                        data = json.loads(line.decode("utf-8"))
                        chunk = data.get("response", "")
                        if chunk:
                            self.chunk.emit(chunk)
                    except Exception as e:
                        self.error.emit(f"Stream parse error: {e}")
                        break
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))
