"""
GUI do app e faz:

1. Coleta de dados do usuário (contato, mensagem, arquivo, data/hora)
2. Valida inputs
3. Envia imediatamente OU agenda para depois
4. Integra com core.db e core.scheduler
"""
import os
import sys
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QLineEdit, QTextEdit,
    QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
    QMessageBox, QComboBox, QDateTimeEdit, QProgressDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QTabWidget
)
from PySide6.QtCore import QDateTime, Qt, QThread, Signal
from PySide6.QtGui import QIcon

# Importa módulos do core
from core.scheduler import create_windows_task, delete_windows_task
from core.db import db
from core import automation


# =============================
# FUNÇÕES AUXILIARES
# =============================
def _get_icon_path() -> Path:
    """Retorna caminho do ícone do app"""
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent.absolute()
    
    return base / "resources" / "Taty_s-English-Logo.ico"


def _get_profile_dir() -> Path:
    """Retorna diretório do perfil Chrome"""
    if getattr(sys, 'frozen', False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).parent.parent.absolute()
    
    profile_dir = base / "chrome_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    return profile_dir


# =============================
# WORKER THREAD (para não travar UI)
# =============================
class AutomationWorker(QThread):
    """Thread separada para executar automação sem travar a interface"""
    
    log_signal = Signal(str)
    finished_signal = Signal(bool, str)  # (sucesso, mensagem)
    
    def __init__(self, userdir, target, mode, message=None, file_path=None):
        super().__init__()
        self.userdir = userdir
        self.target = target
        self.mode = mode
        self.message = message
        self.file_path = file_path
    
    def run(self):
        """Executa automação em thread separada"""
        try:
            def logger(msg):
                self.log_signal.emit(msg)
            
            automation.executar_envio(
                userdir=str(self.userdir),
                target=self.target,
                mode=self.mode,
                message=self.message,
                file_path=self.file_path,
                logger=logger,
                headless=False  # Mostra navegador para debug
            )
            
            self.finished_signal.emit(True, "✓ Mensagem enviada com sucesso!")
            
        except Exception as e:
            self.finished_signal.emit(False, f"✗ Erro: {str(e)}")


# =============================
# JANELA PRINCIPAL
# =============================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Study Practices - WhatsApp Automação v2.0")
        self.setMinimumSize(700, 750)
        
        self.file_path = None
        self.worker = None  # Thread de automação
        
        # Define ícone
        icon_path = _get_icon_path()
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
        
        self._build_ui()
    
    # =============================
    # CONSTRUÇÃO DA UI
    # =============================
    def _build_ui(self):
        """Constrói interface com abas"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title = QLabel("📱 Automação de WhatsApp")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #00a884;")
        layout.addWidget(title)
        
        # Sistema de Abas
        tabs = QTabWidget()
        tabs.addTab(self._create_send_tab(), "📤 Enviar")
        tabs.addTab(self._create_history_tab(), "📋 Histórico")
        
        layout.addWidget(tabs)
        central.setLayout(layout)
    
    def _create_send_tab(self) -> QWidget:
        """Cria aba de envio"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # ===== CONTATO =====
        layout.addWidget(QLabel("🎯 Contato / Número:"))
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Ex: João Silva ou 5511999999999")
        layout.addWidget(self.target_input)
        
        # ===== MODO =====
        layout.addWidget(QLabel("📋 Modo de envio:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("📝 Somente texto", "text")
        self.mode_combo.addItem("📎 Somente arquivo", "file")
        self.mode_combo.addItem("📎📝 Arquivo + texto", "file_text")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_change)
        layout.addWidget(self.mode_combo)
        
        # ===== MENSAGEM =====
        layout.addWidget(QLabel("💬 Mensagem:"))
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Digite sua mensagem aqui...")
        self.message_input.setMaximumHeight(150)
        layout.addWidget(self.message_input)
        
        # ===== ARQUIVO =====
        file_layout = QHBoxLayout()
        self.file_btn = QPushButton("📎 Selecionar Arquivo")
        self.file_btn.clicked.connect(self._select_file)
        self.file_label = QLabel("Nenhum arquivo selecionado")
        self.file_label.setStyleSheet("color: #888;")
        file_layout.addWidget(self.file_btn)
        file_layout.addWidget(self.file_label, 1)
        layout.addLayout(file_layout)
        
        # ===== DATA/HORA =====
        layout.addWidget(QLabel("🕒 Data e hora do envio:"))
        self.datetime_picker = QDateTimeEdit()
        self.datetime_picker.setCalendarPopup(True)
        self.datetime_picker.setDisplayFormat("dd/MM/yyyy HH:mm")
        
        # Define hora mínima como agora + 1 minuto
        min_datetime = QDateTime.currentDateTime().addSecs(60)
        self.datetime_picker.setMinimumDateTime(min_datetime)
        self.datetime_picker.setDateTime(min_datetime)
        layout.addWidget(self.datetime_picker)
        
        # ===== BOTÕES =====
        buttons_layout = QHBoxLayout()
        
        self.send_now_btn = QPushButton("▶ Enviar Agora")
        self.send_now_btn.setStyleSheet("""
            QPushButton {
                background-color: #00a884;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #008f6d;
            }
        """)
        self.send_now_btn.clicked.connect(self._send_now)
        buttons_layout.addWidget(self.send_now_btn)
        
        self.schedule_btn = QPushButton("⏰ Agendar")
        self.schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #0088cc;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #006699;
            }
        """)
        self.schedule_btn.clicked.connect(self._schedule_task)
        buttons_layout.addWidget(self.schedule_btn)
        
        layout.addLayout(buttons_layout)
        
        # ===== INSTRUÇÕES =====
        instructions = QLabel(
            "💡 <b>Dicas:</b><br>"
            "• Para números, use código do país (Ex: 5511999999999)<br>"
            "• Certifique-se de fazer login no WhatsApp Web antes de usar<br>"
            "• Agendamentos requerem que o computador esteja ligado"
        )
        instructions.setStyleSheet("color: #888; font-size: 11px; margin-top: 10px;")
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        layout.addStretch()
        tab.setLayout(layout)
        
        # Atualiza estado inicial
        self._on_mode_change()
        
        return tab
    
    def _create_history_tab(self) -> QWidget:
        """Cria aba de histórico"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("📋 Histórico de Agendamentos")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Tabela
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Contato", "Modo", "Data/Hora", "Status", "Ações"
        ])
        
        # Configura largura das colunas
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Contato expande
        
        layout.addWidget(self.history_table)
        
        # Botão atualizar
        refresh_btn = QPushButton("🔄 Atualizar")
        refresh_btn.clicked.connect(self._refresh_history)
        layout.addWidget(refresh_btn)
        
        tab.setLayout(layout)
        
        # Carrega dados iniciais
        self._refresh_history()
        
        return tab
    
    # =============================
    # EVENTOS
    # =============================
    def _on_mode_change(self):
        """Habilita/desabilita campos conforme modo"""
        mode = self.mode_combo.currentData()
        
        if mode == "text":
            self.message_input.setEnabled(True)
            self.file_btn.setEnabled(False)
            self.message_input.setStyleSheet("")
        
        elif mode == "file":
            self.message_input.setEnabled(False)
            self.file_btn.setEnabled(True)
            self.message_input.setStyleSheet("background-color: #1a1a1a;")
        
        elif mode == "file_text":
            self.message_input.setEnabled(True)
            self.file_btn.setEnabled(True)
            self.message_input.setStyleSheet("")
    
    def _select_file(self):
        """Abre diálogo para selecionar arquivo"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo",
            "",
            "Todos os arquivos (*.*)"
        )
        
        if path:
            self.file_path = path
            filename = os.path.basename(path)
            self.file_label.setText(f"✓ {filename}")
            self.file_label.setStyleSheet("color: #00a884;")
    
    # =============================
    # ENVIAR AGORA
    # =============================
    def _send_now(self):
        """Envia mensagem imediatamente"""
        target = self.target_input.text().strip()
        mode = self.mode_combo.currentData()
        message = self.message_input.toPlainText().strip()
        file_path = self.file_path
        
        # Validação
        if not self._validate_fields(target, mode, message, file_path):
            return
        
        # Confirmação
        reply = QMessageBox.question(
            self,
            "Confirmar Envio",
            f"Deseja enviar para <b>{target}</b> agora?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Desabilita botões
        self.send_now_btn.setEnabled(False)
        self.schedule_btn.setEnabled(False)
        
        # Progress dialog
        self.progress = QProgressDialog("Iniciando automação...", "Cancelar", 0, 0, self)
        self.progress.setWindowModality(Qt.WindowModal)
        self.progress.setWindowTitle("Enviando")
        self.progress.setCancelButton(None)
        self.progress.show()
        
        # Cria worker thread
        profile_dir = _get_profile_dir()
        self.worker = AutomationWorker(
            userdir=profile_dir,
            target=target,
            mode=mode,
            message=message if mode in ("text", "file_text") else None,
            file_path=file_path if mode in ("file", "file_text") else None
        )
        
        # Conecta sinais
        self.worker.log_signal.connect(self._on_worker_log)
        self.worker.finished_signal.connect(self._on_worker_finished)
        
        # Inicia thread
        self.worker.start()
    
    def _on_worker_log(self, msg: str):
        """Atualiza progress dialog com logs"""
        self.progress.setLabelText(msg)
    
    def _on_worker_finished(self, success: bool, message: str):
        """Callback quando automação termina"""
        self.progress.close()
        
        # Reabilita botões
        self.send_now_btn.setEnabled(True)
        self.schedule_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Sucesso", message)
            self._clear_form()
        else:
            QMessageBox.critical(
                self,
                "Erro no Envio",
                f"{message}\n\n"
                "Verifique se o WhatsApp Web está logado."
            )
    
    # =============================
    # AGENDAR
    # =============================
    def _schedule_task(self):
        """Agenda envio para data/hora futura"""
        target = self.target_input.text().strip()
        mode = self.mode_combo.currentData()
        message = self.message_input.toPlainText().strip()
        file_path = self.file_path
        
        # Pega data/hora
        dt = self.datetime_picker.dateTime().toPython()
        scheduled_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Validação
        if not self._validate_fields(target, mode, message, file_path):
            return
        
        # Verifica se data é futura
        if dt <= datetime.now():
            QMessageBox.warning(
                self,
                "Data Inválida",
                "A data/hora deve ser no futuro!"
            )
            return
        
        # Confirmação
        reply = QMessageBox.question(
            self,
            "Confirmar Agendamento",
            f"Agendar envio para <b>{target}</b> em:<br>"
            f"<b>{dt.strftime('%d/%m/%Y às %H:%M')}</b>?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            # Gera nome único
            import time
            task_name = f"SP_WA_{int(time.time())}"
            
            # 1. Salva no banco PRIMEIRO
            task_id = db.adicionar(
                task_name=task_name,
                target=target,
                mode=mode,
                scheduled_time=dt,
                message=message if mode in ("text", "file_text") else None,
                file_path=file_path if mode in ("file", "file_text") else None
            )
            
            if task_id < 0:
                raise Exception("Erro ao salvar no banco de dados")
            
            # 2. Cria tarefa no Windows Task Scheduler
            create_windows_task(
                task_id=task_id,
                scheduled_time=scheduled_time,
                target=target,
                mode=mode,
                message=message if mode in ("text", "file_text") else None,
                file_path=file_path if mode in ("file", "file_text") else None
            )
            
            QMessageBox.information(
                self,
                "Agendamento Criado",
                f"✓ Tarefa agendada com sucesso!<br><br>"
                f"<b>ID:</b> {task_id}<br>"
                f"<b>Data/Hora:</b> {dt.strftime('%d/%m/%Y às %H:%M')}<br>"
                f"<b>Contato:</b> {target}"
            )
            
            self._clear_form()
            self._refresh_history()  # Atualiza histórico
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erro no Agendamento",
                f"Ocorreu um erro:<br><br>{str(e)}<br><br>"
                "Verifique se o aplicativo está rodando como administrador."
            )
            print(f"Erro: {e}")
            import traceback
            traceback.print_exc()
    
    # =============================
    # HISTÓRICO
    # =============================
    def _refresh_history(self):
        """Atualiza tabela de histórico"""
        try:
            # Busca dados do banco
            tasks = db.listar_todos()
            
            # Limpa tabela
            self.history_table.setRowCount(0)
            
            # Preenche tabela
            for row_idx, task in enumerate(tasks):
                self.history_table.insertRow(row_idx)
                
                # ID
                self.history_table.setItem(row_idx, 0, 
                    QTableWidgetItem(str(task[0])))
                
                # Contato
                self.history_table.setItem(row_idx, 1,
                    QTableWidgetItem(task[2]))
                
                # Modo
                mode_text = {
                    'text': '📝 Texto',
                    'file': '📎 Arquivo',
                    'file_text': '📎📝 Ambos'
                }.get(task[3], task[3])
                self.history_table.setItem(row_idx, 2,
                    QTableWidgetItem(mode_text))
                
                # Data/Hora
                dt = datetime.fromisoformat(task[4])
                self.history_table.setItem(row_idx, 3,
                    QTableWidgetItem(dt.strftime('%d/%m/%Y %H:%M')))
                
                # Status
                status_text = {
                    'pending': '⏳ Pendente',
                    'running': '▶️ Executando',
                    'completed': '✅ Concluído',
                    'failed': '❌ Falhou'
                }.get(task[5], task[5])
                self.history_table.setItem(row_idx, 4,
                    QTableWidgetItem(status_text))
                
                # Botão deletar (apenas para pendentes)
                if task[5] == 'pending':
                    delete_btn = QPushButton("🗑️ Deletar")
                    delete_btn.clicked.connect(
                        lambda checked, tid=task[0]: self._delete_task(tid)
                    )
                    self.history_table.setCellWidget(row_idx, 5, delete_btn)
        
        except Exception as e:
            print(f"Erro ao atualizar histórico: {e}")
    
    def _delete_task(self, task_id: int):
        """Deleta um agendamento"""
        reply = QMessageBox.question(
            self,
            "Confirmar Exclusão",
            f"Deseja realmente cancelar o agendamento ID {task_id}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Remove do Task Scheduler
                delete_windows_task(task_id)
                
                # Remove do banco
                db.deletar(task_id)
                
                QMessageBox.information(
                    self,
                    "Agendamento Cancelado",
                    f"✓ Agendamento ID {task_id} foi cancelado."
                )
                
                self._refresh_history()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao cancelar: {str(e)}"
                )
    
    # =============================
    # VALIDAÇÃO
    # =============================
    def _validate_fields(self, target, mode, message, file_path) -> bool:
        """Valida campos do formulário"""
        if not target:
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "Por favor, informe o contato ou número."
            )
            return False
        
        if mode == "text" and not message:
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "Por favor, digite uma mensagem."
            )
            return False
        
        if mode == "file" and not file_path:
            QMessageBox.warning(
                self,
                "Campo Obrigatório",
                "Por favor, selecione um arquivo."
            )
            return False
        
        if mode == "file_text":
            if not message or not file_path:
                QMessageBox.warning(
                    self,
                    "Campos Obrigatórios",
                    "Por favor, informe mensagem E arquivo."
                )
                return False
        
        return True
    
    # =============================
    # UTILITÁRIOS
    # =============================
    def _clear_form(self):
        """Limpa formulário"""
        self.target_input.clear()
        self.message_input.clear()
        self.file_label.setText("Nenhum arquivo selecionado")
        self.file_label.setStyleSheet("color: #888;")
        self.file_path = None
        
        # Reseta data/hora
        min_datetime = QDateTime.currentDateTime().addSecs(60)
        self.datetime_picker.setDateTime(min_datetime)