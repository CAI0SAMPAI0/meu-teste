# app.py
import sys
import json
import os
from datetime import datetime
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow

BASE_DIR = getattr(
    sys,
    "_MEIPASS",
    os.path.abspath(os.path.dirname(__file__))
)

PROFILE_DIR = os.path.join(BASE_DIR, "chrome_profile")

def ensure_profile_dir():
    os.makedirs(PROFILE_DIR, exist_ok=True)

# Logger para execução automática
def get_file_logger():
    logs_dir = os.path.join(BASE_DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    log_path = os.path.join(
        logs_dir,
        f"auto_{datetime.now().strftime('%Y-%m-%d')}.log"
    )

    def logger(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        print(line.strip())  # ← ADICIONADO: também imprime no console
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)

    return logger

def run_gui():
    ensure_profile_dir()

    app = QApplication(sys.argv)

    # Ícone (Windows)
    from PySide6.QtGui import QIcon
    icon_path = os.path.join(BASE_DIR, "resources", "Taty_s-English-Logo.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "WhatsAppAutomation"
                )
            except Exception:
                pass

    qss_path = os.path.join(BASE_DIR, "ui", "styles.qss")
    if os.path.exists(qss_path):
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

# Execução Automática (Task Scheduler)
def run_auto(json_path: str):
    ensure_profile_dir()
    logger = get_file_logger()

    logger("=" * 70)
    logger("INÍCIO DA AUTOMAÇÃO AGENDADA")
    logger(f"Arquivo de instrução: {json_path}")
    logger(f"Diretório de trabalho: {os.getcwd()}")
    logger(f"BASE_DIR: {BASE_DIR}")
    logger("=" * 70)

    # =============================
    # VALIDAÇÃO DO ARQUIVO JSON
    # =============================
    if not os.path.exists(json_path):
        logger(f"❌ ERRO: Arquivo não encontrado: {json_path}")
        logger(f"   Diretório atual: {os.getcwd()}")
        logger(f"   Arquivos na pasta: {os.listdir(os.path.dirname(json_path) if os.path.dirname(json_path) else '.')}")
        sys.exit(1)

    logger(f"✓ Arquivo JSON encontrado")

    # =============================
    # LEITURA DO JSON
    # =============================
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger(f"✓ JSON carregado com sucesso")
        logger(f"   Conteúdo: {data}")
    except Exception as e:
        logger(f"❌ ERRO ao ler JSON: {e}")
        sys.exit(1)

    # =============================
    # EXTRAÇÃO DOS DADOS
    # =============================
    mode = data.get("mode")
    target = data.get("target")
    text = data.get("message")  # ← Pode ser vazio
    file_path = data.get("file")  # ← CORRIGIDO: era "file_path", agora é "file"

    logger(f"Target: {target}")
    logger(f"Mode: {mode}")
    logger(f"Message: {text if text else '(vazio)'}")
    logger(f"File: {file_path if file_path else '(nenhum)'}")

    # =============================
    # VALIDAÇÃO DOS DADOS
    # =============================
    if not target:
        logger("❌ ERRO: Target não especificado")
        sys.exit(1)

    if not mode:
        logger("❌ ERRO: Mode não especificado")
        sys.exit(1)

    if mode not in ["text", "file", "file_text"]:
        logger(f"❌ ERRO: Mode inválido: {mode}")
        sys.exit(1)

    # Validação específica por modo
    if mode == "text" and not text:
        logger("❌ ERRO: Mode 'text' requer mensagem")
        sys.exit(1)

    if mode in ["file", "file_text"] and not file_path:
        logger("❌ ERRO: Mode requer arquivo mas file_path está vazio")
        sys.exit(1)

    if mode in ["file", "file_text"] and not os.path.exists(file_path):
        logger(f"❌ ERRO: Arquivo não encontrado: {file_path}")
        sys.exit(1)

    logger("✓ Validações concluídas")

    # =============================
    # EXECUÇÃO DA AUTOMAÇÃO
    # =============================
    try:
        logger("Importando módulo de automação...")
        from core import automation

        logger("Iniciando execução...")
        automation.executar_envio(
            userdir=PROFILE_DIR,
            target=target,
            mode=mode,
            message=text if text else None,
            file_path=file_path if file_path else None,
            logger=logger
        )

        logger("=" * 70)
        logger("✓ AUTOMAÇÃO FINALIZADA COM SUCESSO")
        logger("=" * 70)
        sys.exit(0)

    except Exception as e:
        logger("=" * 70)
        logger(f"❌ ERRO CRÍTICO: {e}")
        logger("=" * 70)
        
        import traceback
        logger("Traceback completo:")
        logger(traceback.format_exc())
        
        sys.exit(1)

# Entry Point
if __name__ == "__main__":
    # Debug: mostra argumentos recebidos
    if "--auto" in sys.argv:
        print(f"DEBUG: sys.argv = {sys.argv}")
    
    if len(sys.argv) >= 3 and sys.argv[1] == "--auto":
        run_auto(sys.argv[2])
    else:
        run_gui()