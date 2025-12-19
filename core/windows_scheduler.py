import subprocess
import os
import sys
from datetime import datetime


def create_windows_task(task_id: int, scheduled_time: str):
    """
    scheduled_time: yyyy-MM-dd HH:mm:ss
    """

    dt = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M:%S")

    run_date = dt.strftime("%d/%m/%Y")
    run_time = dt.strftime("%H:%M")

    # Detecta se é EXE ou DEV
    
    if getattr(sys, 'frozen', False):
        # Estamos no EXE
        base_dir = os.path.dirname(sys.executable)
        executor_path = os.path.join(base_dir, "executor.exe")
        task_command = f'"{executor_path}" {task_id}'
    else:
        # Ambiente de desenvolvimento
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        executor_path = os.path.join(project_root, "executor.py")
        python_exec = sys.executable
        task_command = f'"{python_exec}" "{executor_path}" {task_id}'

    task_name = f"WA_Automation_Task_{task_id}"

    command = [
        "schtasks",
        "/Create",
        "/F",
        "/SC", "ONCE",
        "/SD", run_date,
        "/ST", run_time,
        "/TN", task_name,
        "/TR", task_command,
        "/RL", "LIMITED"
    ]

    subprocess.run(command, check=True)

