#!/usr/bin/env python3
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

import requests
import threading
import json
import subprocess

OLLAMA_MODEL = "mistral"


def copy_to_clipboard(text):
    subprocess.run(["wl-copy"], input=text.encode())

def get_clipboard():
    result = subprocess.run(["wl-paste", "--primary"], capture_output=True, text=True)
    return result.stdout.strip()


class CorrectionWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Correction AI")
        self.set_border_width(10)
        self.set_default_size(600, 300)
        self.set_type_hint(Gdk.WindowTypeHint.POPUP_MENU)
        # self.set_decorated(False)
        self.set_keep_above(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        
        Gtk.Settings.get_default().set_property('gtk-application-prefer-dark-theme', True)
        
        self.clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        # self.clipboard.request_text(self.on_clipboard_text_received)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(self.vbox)

        self.original_label = Gtk.Label(label="📝 Texte original :")
        self.original_label.set_xalign(0)
        self.vbox.pack_start(self.original_label, False, False, 0)

        self.original_view = Gtk.TextView()
        self.original_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.original_view.set_editable(False)
        self.vbox.pack_start(self.original_view, True, True, 0)

        self.corrected_label = Gtk.Label(label="🧠 Correction en cours...")
        self.corrected_label.set_xalign(0)
        self.vbox.pack_start(self.corrected_label, False, False, 0)

        self.corrected_view = Gtk.TextView()
        self.corrected_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.corrected_buffer = self.corrected_view.get_buffer()
        self.corrected_view.set_editable(False)
        self.vbox.pack_start(self.corrected_view, True, True, 0)

        self.copy_button = Gtk.Button(label="📋 Copier le texte corrigé")
        self.copy_button.set_sensitive(False)
        self.copy_button.connect("clicked", self.copy_corrected_text)
        self.vbox.pack_start(self.copy_button, False, False, 0)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

        GLib.idle_add(self.load_clipboard_text)

    def load_clipboard_text(self):
        text = get_clipboard()
        if not text:
            self.show_error("Aucun texte trouvé dans le presse-papier.")
            return

        self.original_view.get_buffer().set_text(text)
        threading.Thread(target=self.start_correction_stream, args=(text,), daemon=True).start()

    def start_correction_stream(self, input_text):
        prompt = f"Corrige la grammaire et l’orthographe de ce texte en français. Réponds uniquement avec le texte corrigé :\n\n\"{input_text}\""
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": True
        }

        try:
            with requests.post(url, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line.decode("utf-8"))
                        chunk = data.get("response", "")
                        GLib.idle_add(self.append_text, chunk)
                GLib.idle_add(self.on_correction_done)
        except Exception as e:
            GLib.idle_add(self.show_error, f"Erreur : {e}")

    def append_text(self, text):
        end_iter = self.corrected_buffer.get_end_iter()
        self.corrected_buffer.insert(end_iter, text)

    def on_correction_done(self):
        self.corrected_label.set_text("✅ Texte corrigé :")
        self.copy_button.set_sensitive(True)

    def copy_corrected_text(self, widget):
        start, end = self.corrected_buffer.get_bounds()
        corrected_text = self.corrected_buffer.get_text(start, end, True)

        copy_to_clipboard(corrected_text)
        # self.clipboard.set_text(corrected_text, -1)
        Gtk.main_quit()

    def show_error(self, message):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text="Erreur",
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
        Gtk.main_quit()


def main():
    win = CorrectionWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
