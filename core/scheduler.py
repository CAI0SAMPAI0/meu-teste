"""
Sistema de agendamento usando Windows Task Scheduler.

Fluxo CORRIGIDO:
1. Criar arquivo JSON com instruções de envio
2. Criar tarefa no Windows Task Scheduler
3. Na hora agendada, Task Scheduler executa: app.py --auto caminho.json
4. app.py lê o JSON e executa a automação
"""

import subprocess
import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional


# =============================
# CONFIGURAÇÃO DE CAMINHOS
# =============================
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.parent.absolute()

TASKS_DIR = BASE_DIR / "scheduled_tasks"
TASKS_DIR.mkdir(parents=True, exist_ok=True)

# Diretório de logs para debug
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def create_task_json(
    task_id: int,
    target: str,
    mode: str,
    message: Optional[str] = None,
    file_path: Optional[str] = None
) -> Path:
    """
    Cria arquivo JSON com instruções para execução automática.
    """
    json_filename = f"task_{task_id}.json"
    json_path = TASKS_DIR / json_filename
    
    task_data = {
        "task_id": task_id,
        "target": target,
        "mode": mode,
        "message": message or "",
        "file": file_path or ""  # ← CORRIGIDO: era "file_path", agora é "file"
    }
    
    # Salva JSON com encoding UTF-8
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(task_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ JSON criado: {json_path}")
    print(f"  Conteúdo: {task_data}")
    return json_path


def create_windows_task(
    task_id: int,
    scheduled_time: str,
    target: str,
    mode: str,
    message: Optional[str] = None,
    file_path: Optional[str] = None
) -> bool:
    """
    Cria tarefa agendada no Windows Task Scheduler.
    """
    
    # =============================
    # 1. CRIA JSON DE INSTRUÇÃO
    # =============================
    json_path = create_task_json(task_id, target, mode, message, file_path)
    
    # =============================
    # 2. FORMATA DATA/HORA PARA SCHTASKS
    # =============================
    dt = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M:%S")
    run_date = dt.strftime("%d/%m/%Y")
    run_time = dt.strftime("%H:%M")
    
    # =============================
    # 3. DETERMINA EXECUTÁVEL E CAMINHOS
    # =============================
    if getattr(sys, 'frozen', False):
        # Modo EXE (PyInstaller)
        exe_path = sys.executable
        app_path = None
        python_exe = None
    else:
        # Modo desenvolvimento
        exe_path = None
        python_exe = sys.executable
        app_path = BASE_DIR / "app.py"
    
    task_name = f"StudyPractices_WA_{task_id}"
    
    # =============================
    # 4. CRIA ARQUIVO BAT (mais confiável)
    # =============================
    bat_path = TASKS_DIR / f"task_{task_id}.bat"
    
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("chcp 65001 > nul\n")
        
        # Navega para o diretório correto
        f.write(f'cd /d "{BASE_DIR}"\n')
        
        # Log inicial
        f.write(f'echo ============================================ > "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        f.write(f'echo INICIO DA TAREFA {task_id} >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        f.write(f'echo Data/Hora: %date% %time% >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        f.write(f'echo Diretorio: %CD% >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        f.write(f'echo ============================================ >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        f.write(f'echo. >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        
        # Log geral
        f.write(f'echo [%date% %time%] Iniciando tarefa {task_id} >> "{LOGS_DIR / "scheduler.log"}"\n')
        
        # Comando principal
        if getattr(sys, 'frozen', False):
            f.write(f'"{exe_path}" --auto "{json_path}" >> "{LOGS_DIR / f"task_{task_id}.log"}" 2>&1\n')
        else:
            f.write(f'"{python_exe}" "{app_path}" --auto "{json_path}" >> "{LOGS_DIR / f"task_{task_id}.log"}" 2>&1\n')
        
        # Captura código de saída
        f.write(f'set EXIT_CODE=%ERRORLEVEL%\n')
        f.write(f'echo. >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        f.write(f'echo ============================================ >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        f.write(f'echo FIM DA TAREFA {task_id} >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        f.write(f'echo Codigo de saida: %EXIT_CODE% >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        f.write(f'echo ============================================ >> "{LOGS_DIR / f"task_{task_id}.log"}"\n')
        
        # Log geral
        f.write(f'echo [%date% %time%] Tarefa {task_id} finalizada (codigo: %EXIT_CODE%) >> "{LOGS_DIR / "scheduler.log"}"\n')
        
        # Retorna código de saída
        f.write(f'exit /b %EXIT_CODE%\n')
    
    print(f"✓ Arquivo BAT criado: {bat_path}")
    
    # =============================
    # 5. MONTA COMANDO SCHTASKS
    # =============================
    schtasks_command = [
        "schtasks",
        "/Create",
        "/F",
        "/SC", "ONCE",
        "/SD", run_date,
        "/ST", run_time,
        "/TN", task_name,
        "/TR", f'"{bat_path}"',  # ← USA O BAT em vez do comando direto
        "/RL", "HIGHEST"
    ]
    
    # =============================
    # 6. EXECUTA COMANDO
    # =============================
    print(f"\n{'='*60}")
    print(f"CRIANDO TAREFA AGENDADA NO WINDOWS")
    print(f"{'='*60}")
    print(f"Nome: {task_name}")
    print(f"Data/Hora: {run_date} {run_time}")
    print(f"BAT: {bat_path}")
    print(f"JSON: {json_path}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            schtasks_command,
            check=True,
            shell=False,
            capture_output=True,
            text=True,
            encoding='latin-1'
        )
        
        print("✓ Tarefa criada com sucesso no Task Scheduler!")
        print(f"\n📝 Para testar manualmente:")
        print(f"   schtasks /Run /TN {task_name}")
        print(f"\n📋 Para ver detalhes:")
        print(f"   schtasks /Query /TN {task_name} /V /FO LIST")
        print(f"\n📁 Logs em: {LOGS_DIR}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        error_msg = f"Erro ao criar tarefa no Windows:\n"
        error_msg += f"Código: {e.returncode}\n"
        if e.stdout:
            error_msg += f"Saída: {e.stdout}\n"
        if e.stderr:
            error_msg += f"Erro: {e.stderr}"
        
        print(f"✗ {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        raise


def delete_windows_task(task_id: int) -> bool:
    """Remove tarefa do Windows Task Scheduler."""
    task_name = f"StudyPractices_WA_{task_id}"
    
    command = [
        "schtasks",
        "/Delete",
        "/TN", task_name,
        "/F"
    ]
    
    try:
        subprocess.run(
            command,
            check=True,
            shell=False,
            capture_output=True,
            text=True,
            encoding='latin-1'
        )
        
        print(f"✓ Tarefa removida do Task Scheduler: {task_name}")
        
        # Remove arquivos associados
        json_path = TASKS_DIR / f"task_{task_id}.json"
        bat_path = TASKS_DIR / f"task_{task_id}.bat"
        
        if json_path.exists():
            json_path.unlink()
            print(f"✓ JSON removido: {json_path}")
        
        if bat_path.exists():
            bat_path.unlink()
            print(f"✓ BAT removido: {bat_path}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Tarefa {task_name} não encontrada ou erro ao remover")
        return False
    except Exception as e:
        print(f"⚠️  Erro ao deletar: {e}")
        return False


def test_task_execution(task_id: int) -> bool:
    """
    Testa a execução de uma tarefa imediatamente.
    Útil para debug.
    """
    task_name = f"StudyPractices_WA_{task_id}"
    
    command = [
        "schtasks",
        "/Run",
        "/TN", task_name
    ]
    
    try:
        print(f"\n🧪 Testando execução da tarefa {task_id}...")
        print(f"   Aguarde alguns segundos...")
        
        subprocess.run(
            command,
            check=True,
            shell=False,
            capture_output=True,
            text=True,
            encoding='latin-1'
        )
        
        print(f"✓ Tarefa iniciada!")
        print(f"📋 Verifique o log em: {LOGS_DIR / f'task_{task_id}.log'}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Erro ao executar tarefa: {e.stderr if e.stderr else 'Desconhecido'}")
        return False


def list_windows_tasks() -> list:
    """Lista todas as tarefas do Study Practices."""
    command = [
        "schtasks",
        "/Query",
        "/FO", "LIST",
        "/V"
    ]
    
    try:
        result = subprocess.run(
            command,
            check=True,
            shell=False,
            capture_output=True,
            text=True,
            encoding='latin-1'
        )
        
        tasks = []
        for line in result.stdout.split('\n'):
            if "StudyPractices_WA_" in line:
                tasks.append(line.strip())
        
        return tasks
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao listar tarefas: {e.stderr if e.stderr else 'Desconhecido'}")
        return []


def verificar_status_tarefa(task_id: int) -> Optional[str]:
    """Verifica status de uma tarefa específica."""
    task_name = f"StudyPractices_WA_{task_id}"
    
    command = [
        "schtasks",
        "/Query",
        "/TN", task_name,
        "/FO", "LIST",
        "/V"
    ]
    
    try:
        result = subprocess.run(
            command,
            check=True,
            shell=False,
            capture_output=True,
            text=True,
            encoding='latin-1'
        )
        
        for line in result.stdout.split('\n'):
            if "Status:" in line or "Estado:" in line:
                return line.split(":")[-1].strip()
        
        return None
        
    except subprocess.CalledProcessError:
        return None


# =============================
# TESTES
# =============================
if __name__ == "__main__":
    print("Testando sistema de agendamento...")
    
    from datetime import timedelta
    
    test_time = (datetime.now() + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
    test_id = 99999
    
    print(f"\n🧪 Criando tarefa de teste para: {test_time}")
    
    try:
        create_windows_task(
            task_id=test_id,
            scheduled_time=test_time,
            target="5511999999999",
            mode="text",
            message="Mensagem de teste automático"
        )
        
        print("\n✓ Teste concluído!")
        print(f"\n🔍 Para testar agora:")
        print(f"   python -c \"from core.scheduler import test_task_execution; test_task_execution({test_id})\"")
        
    except Exception as e:
        print(f"\n✗ Erro no teste: {e}")