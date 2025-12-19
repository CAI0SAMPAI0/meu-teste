"""
Sistema de agendamento usando Windows Task Scheduler.

Fluxo:
1. Criar arquivo JSON com instruções de envio
2. Criar tarefa no Windows Task Scheduler
3. Na hora agendada, Task Scheduler executa: app.py --auto caminho.json
4. app.py lê o JSON e executa a automação (HEADLESS)
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


def create_task_json(
    task_id: int,
    target: str,
    mode: str,
    message: Optional[str] = None,
    file_path: Optional[str] = None
) -> Path:
    """
    Cria arquivo JSON com instruções para execução automática.
    
    Args:
        task_id: ID único da tarefa
        target: Contato/número
        mode: Tipo de envio
        message: Texto (opcional)
        file_path: Arquivo (opcional)
        
    Returns:
        Path: Caminho do arquivo JSON criado
    """
    json_filename = f"task_{task_id}.json"
    json_path = TASKS_DIR / json_filename
    
    task_data = {
        "task_id": task_id,
        "target": target,
        "mode": mode,
        "message": message or "",
        "file_path": file_path or ""
    }
    
    # Salva JSON com encoding UTF-8
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(task_data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ JSON criado: {json_path}")
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
    A tarefa executará o app em modo --auto (headless).
    
    Args:
        task_id: ID único da tarefa
        scheduled_time: Data/hora no formato "YYYY-MM-DD HH:MM:SS"
        target: Contato/número
        mode: Tipo de envio
        message: Texto (opcional)
        file_path: Arquivo (opcional)
        
    Returns:
        bool: True se criou com sucesso
        
    Raises:
        Exception: Se falhar ao criar tarefa
    """
    
    # =============================
    # 1. CRIA JSON DE INSTRUÇÃO
    # =============================
    json_path = create_task_json(task_id, target, mode, message, file_path)
    
    # =============================
    # 2. FORMATA DATA/HORA PARA SCHTASKS
    # =============================
    dt = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M:%S")
    run_date = dt.strftime("%d/%m/%Y")  # Formato brasileiro DD/MM/YYYY
    run_time = dt.strftime("%H:%M")
    
    # =============================
    # 3. DETERMINA COMANDO A EXECUTAR
    # =============================
    if getattr(sys, 'frozen', False):
        # Se for executável (.exe) compilado com PyInstaller
        exe_path = sys.executable
        task_command = f'"{exe_path}" --auto "{json_path}"'
    else:
        # Se for script Python em desenvolvimento
        python_exe = sys.executable
        app_path = BASE_DIR / "app.py"
        task_command = f'"{python_exe}" "{app_path}" --auto "{json_path}"'
    
    # Nome único da tarefa
    task_name = f"StudyPractices_WA_{task_id}"
    
    # =============================
    # 4. MONTA COMANDO SCHTASKS
    # =============================
    schtasks_command = [
        "schtasks",
        "/Create",
        "/F",  # Force: sobrescreve se já existir
        "/SC", "ONCE",  # Schedule: uma única vez
        "/SD", run_date,  # Start Date
        "/ST", run_time,  # Start Time
        "/TN", task_name,  # Task Name
        "/TR", task_command,  # Task Run: comando a executar
        "/RL", "HIGHEST"  # Run Level: privilégios mais altos (necessário para automação)
    ]
    
    # =============================
    # 5. EXECUTA COMANDO
    # =============================
    print(f"\n{'='*60}")
    print(f"CRIANDO TAREFA AGENDADA NO WINDOWS")
    print(f"{'='*60}")
    print(f"Nome: {task_name}")
    print(f"Data/Hora: {run_date} {run_time}")
    print(f"Comando: {task_command}")
    print(f"Modo: HEADLESS (automático)")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            schtasks_command,
            check=True,
            shell=False,
            capture_output=True,
            text=True,
            encoding='latin-1'  # Windows usa latin-1 por padrão
        )
        
        print("✓ Tarefa criada com sucesso no Task Scheduler!")
        if result.stdout:
            print(f"Output: {result.stdout}")
        
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
    """
    Remove tarefa do Windows Task Scheduler.
    
    Args:
        task_id: ID da tarefa
        
    Returns:
        bool: True se removeu, False se não encontrou
    """
    task_name = f"StudyPractices_WA_{task_id}"
    
    command = [
        "schtasks",
        "/Delete",
        "/TN", task_name,
        "/F"  # Force: não pede confirmação
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
        
        # Remove JSON também
        json_path = TASKS_DIR / f"task_{task_id}.json"
        if json_path.exists():
            json_path.unlink()
            print(f"✓ JSON removido: {json_path}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Tarefa {task_name} não encontrada ou erro ao remover")
        if e.stderr:
            print(f"   Detalhes: {e.stderr}")
        return False
    except Exception as e:
        print(f"⚠️  Erro ao deletar: {e}")
        return False


def list_windows_tasks() -> list:
    """
    Lista todas as tarefas do Study Practices no Task Scheduler.
    
    Returns:
        list: Lista de nomes das tarefas encontradas
    """
    command = [
        "schtasks",
        "/Query",
        "/FO", "LIST",  # Format Output: LIST
        "/V"  # Verbose
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
        
        # Filtra apenas tarefas do nosso app
        tasks = []
        for line in result.stdout.split('\n'):
            if "StudyPractices_WA_" in line:
                tasks.append(line.strip())
        
        return tasks
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao listar tarefas: {e.stderr if e.stderr else 'Desconhecido'}")
        return []
    except Exception as e:
        print(f"Erro ao listar: {e}")
        return []


def verificar_status_tarefa(task_id: int) -> Optional[str]:
    """
    Verifica status de uma tarefa específica.
    
    Args:
        task_id: ID da tarefa
        
    Returns:
        str: Status da tarefa, ou None se não encontrada
            Possíveis valores: "Ready", "Running", "Disabled"
    """
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
        
        # Procura pela linha de status
        for line in result.stdout.split('\n'):
            if "Status:" in line or "Estado:" in line:  # PT/EN
                return line.split(":")[-1].strip()
        
        return None
        
    except subprocess.CalledProcessError:
        return None
    except Exception:
        return None


# =============================
# TESTES (se executado diretamente)
# =============================
if __name__ == "__main__":
    print("Testando sistema de agendamento...")
    print("NOTA: Tarefas agendadas rodarão em HEADLESS\n")
    
    # Cria tarefa de teste para daqui a 2 minutos
    from datetime import timedelta
    
    test_time = (datetime.now() + timedelta(minutes=2)).strftime("%Y-%m-%d %H:%M:%S")
    test_id = 99999  # ID de teste
    
    print(f"\nCriando tarefa de teste para: {test_time}")
    
    try:
        create_windows_task(
            task_id=test_id,
            scheduled_time=test_time,
            target="5511999999999",
            mode="text",
            message="Mensagem de teste automático (HEADLESS)"
        )
        
        print("\n✓ Teste concluído!")
        print(f"  A tarefa executará em HEADLESS (sem mostrar navegador)")
        print(f"  Verifique em 2 minutos se a tarefa executou.")
        print(f"  Log estará em: logs/auto_{datetime.now().strftime('%Y-%m-%d')}.log")
        
    except Exception as e:
        print(f"\n✗ Erro no teste: {e}")