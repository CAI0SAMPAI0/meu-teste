import os
import sys
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit,
    QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
    QMessageBox, QComboBox, QDateTimeEdit
)
from PySide6.QtCore import QDateTime
from PySide6.QtGui import QIcon  # <--- CORREÇÃO APLICADA AQUI

from core.windows_scheduler import create_windows_task
from data.database import create_task
from core import automation

def _get_icon_path():
    base = getattr(sys, "_MEIPASS", os.path.abspath(os.path.dirname(__file__)))
    return os.path.join(base, "resources", "Taty_s-English-Logo.ico")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Study Practices")
        self.setMinimumSize(500, 600)

        self.file_path = None
        icon_path = _get_icon_path()
        
        # O uso de QIcon agora está correto devido à importação acima
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self._build_ui()

    # =====================================================
    # UI
    # =====================================================

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout()

        # ===== CONTATO =====
        layout.addWidget(QLabel("Contato / Número:"))
        self.target_input = QLineEdit()
        layout.addWidget(self.target_input)

        # ===== MODO =====
        layout.addWidget(QLabel("Modo de envio:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("Somente texto", "text")
        self.mode_combo.addItem("Somente arquivo", "file")
        self.mode_combo.addItem("Arquivo + texto", "file_text")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_change)
        layout.addWidget(self.mode_combo)

        # ===== MENSAGEM =====
        layout.addWidget(QLabel("Mensagem:"))
        self.message_input = QTextEdit()
        layout.addWidget(self.message_input)

        # ===== ARQUIVO =====
        file_layout = QHBoxLayout()
        self.file_label = QLabel("Nenhum arquivo selecionado")
        self.file_btn = QPushButton("Selecionar Arquivo")
        self.file_btn.clicked.connect(self._select_file)
        file_layout.addWidget(self.file_btn)
        file_layout.addWidget(self.file_label)
        layout.addLayout(file_layout)

        # ===== DATA/HORA =====
        layout.addWidget(QLabel("Data e hora do envio:"))
        self.datetime_picker = QDateTimeEdit()
        self.datetime_picker.setCalendarPopup(True)
        self.datetime_picker.setDateTime(QDateTime.currentDateTime())
        layout.addWidget(self.datetime_picker)

        # ===== BOTÕES =====
        buttons_layout = QHBoxLayout()

        self.send_now_btn = QPushButton("Enviar agora")
        self.send_now_btn.clicked.connect(self._send_now)
        buttons_layout.addWidget(self.send_now_btn)

        self.schedule_btn = QPushButton("Agendar")
        self.schedule_btn.clicked.connect(self._schedule_task)
        buttons_layout.addWidget(self.schedule_btn)

        layout.addLayout(buttons_layout)

        central.setLayout(layout)

        self._on_mode_change()

    # =====================================================
    # EVENTOS
    # =====================================================

    def _on_mode_change(self):
        mode = self.mode_combo.currentData()

        if mode == "text":
            self.message_input.setEnabled(True)
            self.file_btn.setEnabled(False)

        elif mode == "file":
            self.message_input.setEnabled(False)
            self.file_btn.setEnabled(True)

        elif mode == "file_text":
            self.message_input.setEnabled(True)
            self.file_btn.setEnabled(True)

    def _select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Selecionar arquivo")
        if path:
            self.file_path = path
            self.file_label.setText(os.path.basename(path))

    # =====================================================
    # ENVIAR AGORA
    # =====================================================

    def _send_now(self):
        target = self.target_input.text().strip()
        mode = self.mode_combo.currentData()
        message = self.message_input.toPlainText().strip()
        file_path = self.file_path

        if not self._validate_fields(target, mode, message, file_path):
            return

        def logger(msg):
            print(msg)

        try:
            automation.executar_envio(
                userdir=None,
                target=target,
                mode=mode,
                message=message if mode in ("text", "file_text") else None,
                file_path=file_path if mode in ("file", "file_text") else None,
                logger=logger
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))
            return

        QMessageBox.information(self, "Sucesso", "Mensagem enviada com sucesso.")
        self._clear_form()

    # =====================================================
    # AGENDAR
    # =====================================================

    def _schedule_task(self):
        target = self.target_input.text().strip()
        mode = self.mode_combo.currentData()
        message = self.message_input.toPlainText().strip()
        file_path = self.file_path
        scheduled_time = self.datetime_picker.dateTime().toString(
            "yyyy-MM-dd HH:mm:ss"
        )

        if not self._validate_fields(target, mode, message, file_path):
            return

        task_id = create_task(
            target=target,
            mode=mode,
            message=message if mode in ("text", "file_text") else None,
            file_path=file_path if mode in ("file", "file_text") else None,
            scheduled_time=scheduled_time
        )

        try:
            create_windows_task(task_id, scheduled_time)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro no Agendador do Windows",
                f"Falha ao criar tarefa:\n{e}"
            )
            return

        QMessageBox.information(
            self,
            "Agendamento criado",
            f"Tarefa {task_id} agendada com sucesso."
        )

        self._clear_form()

    # =====================================================
    # VALIDAÇÃO
    # =====================================================

    def _validate_fields(self, target, mode, message, file_path):
        if not target:
            QMessageBox.warning(self, "Erro", "Contato é obrigatório.")
            return False

        if mode == "text" and not message:
            QMessageBox.warning(self, "Erro", "Mensagem obrigatória.")
            return False

        if mode == "file" and not file_path:
            QMessageBox.warning(self, "Erro", "Arquivo obrigatório.")
            return False

        if mode == "file_text" and (not message or not file_path):
            QMessageBox.warning(
                self, "Erro", "Mensagem e arquivo são obrigatórios."
            )
            return False

        return True

    # =====================================================
    # LIMPAR
    # =====================================================

    def _clear_form(self):
        self.target_input.clear()
        self.message_input.clear()
        self.file_label.setText("Nenhum arquivo selecionado")
        self.file_path = None