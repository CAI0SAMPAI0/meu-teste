import sys
import json
import os
from datetime import datetime
from pathlib import Path

# CONFIGURAÇÃO DE ADMIN (Windows)

def is_admin():
    """Verifica se o script está rodando como administrador"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Solicita elevação de privilégios"""
    try:
        import ctypes
        if sys.platform == 'win32':
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas",
                sys.executable, 
                " ".join(sys.argv), 
                None, 
                1 
            )
            sys.exit(0)
    except Exception as e:
        print(f"Erro ao solicitar privilégios de admin: {e}")
        sys.exit(1)

# BASE DIR (dev ou PyInstaller)

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.absolute()

# Adiciona ao path
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.chdir(BASE_DIR)

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

# =============================
# DIRETÓRIOS ESSENCIAIS
# =============================
PROFILE_DIR = BASE_DIR / "chrome_profile"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"
TASKS_DIR = BASE_DIR / "scheduled_tasks"

def ensure_directories():
    """Garante que todos os diretórios necessários existem"""
    for directory in [PROFILE_DIR, LOGS_DIR, DATA_DIR, TASKS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

# LOGGER para execução automática
def get_file_logger():
    """Cria logger que escreve em arquivo"""
    log_path = LOGS_DIR / f"auto_{datetime.now().strftime('%Y-%m-%d')}.log"

    def logger(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}\n"
        
        # Escreve no arquivo
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(line)
        
        # Também imprime no console
        print(line.rstrip())

    return logger

# =============================
# GUI MODE
# =============================
def run_gui():
    """Executa interface gráfica"""
    ensure_directories()

    app = QApplication(sys.argv)

    # Configura ícone do Windows
    icon_path = BASE_DIR / "resources" / "Taty_s-English-Logo.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
        
        # Define App User Model ID (Windows 7+)
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "StudyPractices.WhatsAppAutomation"
                )
            except:
                pass

    # Aplica stylesheet
    qss_path = BASE_DIR / "ui" / "styles.qss"
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    # Importa janela principal (aqui para evitar imports circulares)
    from ui.main_window import MainWindow
    
    window = MainWindow()
    window.show()

    sys.exit(app.exec())

# =============================
# AUTO MODE (executado pelo Task Scheduler)
# =============================
def run_auto(json_path: str):
    """
    Modo automático - executado pelo Windows Task Scheduler
    
    Args:
        json_path: Caminho do arquivo JSON com instruções de envio
    """
    ensure_directories()
    logger = get_file_logger()

    logger("=" * 60)
    logger("INÍCIO DA AUTOMAÇÃO AGENDADA")
    logger(f"BASE_DIR: {BASE_DIR}")
    logger(f"JSON: {json_path}")
    logger("=" * 60)

    # Valida existência do JSON
    json_file = Path(json_path)
    if not json_file.exists():
        logger(f"ERRO: Arquivo de instrução não encontrado!")
        sys.exit(1)

    # Carrega instruções
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        logger(f"ERRO ao ler JSON: {e}")
        sys.exit(1)

    # Extrai dados
    task_id = data.get("task_id")
    target = data.get("target")
    mode = data.get("mode")
    message = data.get("message")
    file_path = data.get("file_path")

    logger(f"Task ID: {task_id}")
    logger(f"Target: {target}")
    logger(f"Mode: {mode}")
    logger(f"Message: {'Sim' if message else 'Não'}")
    logger(f"File: {file_path or 'Nenhum'}")

    # Atualiza status no banco
    try:
        from core.db import db
        db.atualizar_status(task_id, 'running')
    except Exception as e:
        logger(f"Aviso: Não foi possível atualizar status no banco: {e}")

    # Executa automação
    try:
        from core import automation

        automation.executar_envio(
            userdir=str(PROFILE_DIR),
            target=target,
            mode=mode,
            message=message,
            file_path=file_path,
            logger=logger,
            headless=True  # Executar sem mostrar navegador
        )

        logger("✓ AUTOMAÇÃO CONCLUÍDA COM SUCESSO")
        
        # Atualiza banco
        try:
            db.atualizar_status(task_id, 'completed')
        except:
            pass
        
        sys.exit(0)

    except Exception as e:
        logger(f"✗ ERRO DURANTE EXECUÇÃO: {e}")
        
        import traceback
        logger("Traceback completo:")
        logger(traceback.format_exc())
        
        # Registra erro no banco
        try:
            db.atualizar_status(task_id, 'failed', str(e))
        except:
            pass
        
        sys.exit(1)

# =============================
# VERIFICAÇÃO DE INSTÂNCIA ÚNICA
# =============================
def check_single_instance():
    """
    Previne múltiplas instâncias da GUI
    Retorna True se pode continuar, False se deve sair
    """
    import tempfile
    import psutil
    
    lock_file = Path(tempfile.gettempdir()) / "study_practices.lock"
    
    try:
        if lock_file.exists():
            # Lê PID anterior
            old_pid = int(lock_file.read_text())
            
            # Verifica se processo ainda existe
            if psutil.pid_exists(old_pid):
                print("⚠️  Aplicação já está em execução!")
                return False
        
        # Cria novo lock
        lock_file.write_text(str(os.getpid()))
        return True
        
    except Exception as e:
        print(f"Aviso ao verificar instância: {e}")
        return True  # Em caso de erro, permite continuar

def cleanup_lock():
    """Remove arquivo de lock ao sair"""
    import tempfile
    lock_file = Path(tempfile.gettempdir()) / "study_practices.lock"
    try:
        if lock_file.exists():
            lock_file.unlink()
    except:
        pass

# =============================
# ENTRY POINT
# =============================
if __name__ == "__main__":
    # Verifica se está em modo automático
    if len(sys.argv) >= 3 and sys.argv[1] == "--auto":
        # Modo automático NÃO precisa de admin nem lock
        run_auto(sys.argv[2])
    
    else:
        # Modo GUI
        
        # 1. Verifica se é admin (necessário para Task Scheduler)
        if not is_admin():
            print("⚠️  Este aplicativo precisa de privilégios de administrador")
            print("   para criar tarefas agendadas no Windows.")
            print("\n   Solicitando elevação...")
            run_as_admin()
        
        # 2. Verifica instância única
        if not check_single_instance():
            sys.exit(0)
        
        # 3. Executa GUI
        try:
            run_gui()
        finally:
            cleanup_lock()