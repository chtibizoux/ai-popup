from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QTextEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QLineEdit,
    QCompleter,
)

from clipboard_utils import read_text, write_text
from constants import OLLAMA_MODEL, examples
from state import AppState
from worker import StreamWorker


class PromptWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Prompt")
        self.resize(700, 500)

        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        # UI
        layout = QVBoxLayout()

        instruction_label = QLabel("📝 Instruction :")
        layout.addWidget(instruction_label)

        self.instruction_edit = QLineEdit()
        self.instruction_edit.setPlaceholderText("Décrivez la correction ou transformation souhaitée...")
        # default instruction
        self.instruction_edit.setText(examples[0])

        completer = QCompleter(examples, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.instruction_edit.setCompleter(completer)
        layout.addWidget(self.instruction_edit)

        original_label = QLabel("📝 Texte :")
        layout.addWidget(original_label)

        self.original_edit = QTextEdit()
        layout.addWidget(self.original_edit)

        self.start_button = QPushButton("▶️ Démarrer")
        self.start_button.clicked.connect(self.on_primary_button)
        layout.addWidget(self.start_button)

        self.result_label = QLabel("🧠 Réflexion en cours...")
        self.result_label.hide()
        layout.addWidget(self.result_label)

        self.result_edit = QTextEdit()
        self.result_edit.hide()
        layout.addWidget(self.result_edit)

        self.copy_button = QPushButton("📋 Copier le texte")
        self.copy_button.setEnabled(False)
        self.copy_button.clicked.connect(self.copy_result_text)
        self.copy_button.hide()
        layout.addWidget(self.copy_button)

        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget { font-size: 12pt; }
            QTextEdit, QLineEdit { background: #1f1f1f; color: #f1f1f1; }
            QLabel { color: #e0e0e0; }
            QPushButton { padding: 6px 10px; }
            QWidget { background: #121212; }
        """)

        # Worker/thread refs
        self._thread: QThread | None = None
        self._worker: StreamWorker | None = None

        self.state: AppState = AppState.IDLE

        # Enter to start from instruction
        self.instruction_edit.returnPressed.connect(self.on_primary_button)

        self.load_clipboard_text()
        self.apply_state()

    def apply_state(self):
        # Central UI updates based on state
        if self.state == AppState.IDLE:
            self.result_label.hide()
            self.result_edit.hide()
            self.copy_button.hide()
            self.result_edit.setReadOnly(False)
            self.start_button.setText("▶️ Démarrer")
        elif self.state == AppState.RUNNING:
            self.result_label.setText("🧠 Réflexion en cours...")
            self.result_label.show()
            self.result_edit.show()
            self.result_edit.setReadOnly(True)
            self.copy_button.hide()
            self.start_button.setText("⏸️ Annuler")
        elif self.state == AppState.FINISHED:
            self.result_label.setText("✅ Résultat :")
            self.result_label.show()
            self.result_edit.show()
            self.result_edit.setReadOnly(False)
            self.copy_button.show()
            self.copy_button.setEnabled(True)
            self.start_button.setText("🔁 Recommencer")

    def load_clipboard_text(self):
        text = read_text()
        if not text.strip():
            self.show_error("Aucun texte trouvé dans le presse-papier.")
            return
        self.original_edit.setPlainText(text)

    def on_primary_button(self):
        # Button behavior depends on state
        if self.state == AppState.IDLE:
            self.start_processing()
        elif self.state == AppState.RUNNING:
            # cancel
            self.cancel_processing()
        elif self.state == AppState.FINISHED:
            # restart processing using possibly edited result or original? Use original text area content
            self.start_processing()

    def start_processing(self):
        instruction = self.instruction_edit.text().strip()
        input_text = self.original_edit.toPlainText().strip()
        if not input_text:
            self.show_error("Aucun texte d'entrée à traiter.")
            return
        if not instruction:
            self.show_error("Veuillez saisir une instruction.")
            return
        self.result_edit.clear()
        self.state = AppState.RUNNING
        self.apply_state()

        prompt = f"{instruction}\n\n{input_text}"

        # Ensure any previous worker is stopped
        self.teardown_worker()

        # Start new worker thread
        self._thread = QThread(self)
        self._worker = StreamWorker(model=OLLAMA_MODEL, prompt=prompt)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.chunk.connect(self.append_text)
        self._worker.done.connect(self.on_process_done)
        self._worker.error.connect(self.on_error)
        self._thread.start()

    def cancel_processing(self):
        # Stop the worker and reset to IDLE
        self.teardown_worker()
        self.state = AppState.IDLE
        self.apply_state()

    def append_text(self, text: str):
        self.result_edit.moveCursor(self.result_edit.textCursor().MoveOperation.End)
        self.result_edit.insertPlainText(text)
        self.result_edit.moveCursor(self.result_edit.textCursor().MoveOperation.End)

    def on_process_done(self):
        self.teardown_worker()

        self.state = AppState.FINISHED
        self.apply_state()

    def copy_result_text(self):
        text = self.result_edit.toPlainText()
        write_text(text)
        self.close()

    def on_error(self, message: str):
        self.teardown_worker()
        self.show_error(f"Erreur : {message}")

        if self.state == AppState.RUNNING:
            self.state = AppState.IDLE
            self.apply_state()

    def show_error(self, message: str):
        QMessageBox.critical(self, "Erreur", message)

    def teardown_worker(self):
        if self._worker:
            self._worker.stop()
        if self._thread:
            self._thread.quit()
            self._thread.wait(2000)
        self._worker = None
        self._thread = None

    def closeEvent(self, event):
        self.teardown_worker()
        super().closeEvent(event)
