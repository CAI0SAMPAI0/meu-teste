import os
import time

def create_windows_task(task_id, scheduled_time, target, mode, message=None, file_path=None):
    """
    Interface compatível com main_window.py
    Converte os parâmetros e chama o windows_scheduler correto.
    """
    from .windows_scheduler import create_windows_task as create_ws_task
    from .windows_scheduler import create_task_bat
    
    # Prepara nome da tarefa
    task_name = f"WA_Task_{task_id}"
    
    # Prepara dados para o JSON
    task_data = {
        "task_id": str(task_id),
        "task_name": task_name,
        "target": target,
        "mode": mode,
        "message": message if message else "",
        "file_path": file_path if file_path else "",
        "schedule_time": scheduled_time.split()[1] if ' ' in scheduled_time else scheduled_time,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # 1. Cria o arquivo .bat
    create_task_bat(
        task_id=str(task_id),
        task_name=task_name,
        json_config=task_data
    )
    
    # 2. Cria a tarefa no Windows Task Scheduler
    # Extrai apenas a hora (HH:MM) da data completa
    schedule_time_only = scheduled_time.split()[1] if ' ' in scheduled_time else scheduled_time
    
    return create_ws_task(
        task_id=str(task_id),
        task_name=task_name,
        schedule_time=schedule_time_only
    )