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
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {msg}\n")

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

    logger("=== INÍCIO DA AUTOMAÇÃO AGENDADA ===")

    if not os.path.exists(json_path):
        logger(f"Arquivo de instrução não encontrado: {json_path}")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    mode = data.get("mode")
    target = data.get("target")
    text = data.get("text")
    file_path = data.get("file")

    logger(f"Target: {target}")
    logger(f"Mode: {mode}")
    logger(f"File: {file_path}")
    logger(f"Text: {bool(text)}")

    try:
        from core import automation

        automation.executar_envio(
            userdir=PROFILE_DIR,
            target=target,
            mode=mode,
            message=text,
            file_path=file_path,
            logger=logger
        )

        logger("AUTOMAÇÃO FINALIZADA COM SUCESSO")

    except Exception as e:
        logger(f"ERRO CRÍTICO: {e}")
        raise
# Entry Point
if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--auto":
        run_auto(sys.argv[2])
    else:
        run_gui()
