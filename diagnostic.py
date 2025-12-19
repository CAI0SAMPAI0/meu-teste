import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# =============================
# CONFIGURAÇÃO
# =============================
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent.absolute()

TASKS_DIR = BASE_DIR / "scheduled_tasks"
LOGS_DIR = BASE_DIR / "logs"

TASKS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# =============================
# TESTES
# =============================

def test_1_criar_json():
    """Teste 1: Criar JSON de teste"""
    print("\n" + "="*60)
    print("TESTE 1: Criando JSON de instrução")
    print("="*60)
    
    test_json = TASKS_DIR / "test_manual.json"
    
    data = {
        "task_id": 99999,
        "target": "5511999999999",
        "mode": "text",
        "message": "Teste manual de diagnóstico",
        "file": ""
    }
    
    with open(test_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ JSON criado: {test_json}")
    print(f"  Conteúdo: {data}")
    
    return test_json


def test_2_criar_bat():
    """Teste 2: Criar BAT de teste"""
    print("\n" + "="*60)
    print("TESTE 2: Criando arquivo BAT")
    print("="*60)
    
    test_bat = TASKS_DIR / "test_manual.bat"
    test_json = TASKS_DIR / "test_manual.json"
    test_log = LOGS_DIR / "test_manual.log"
    
    if getattr(sys, 'frozen', False):
        exe_path = sys.executable
        comando = f'"{exe_path}" --auto "{test_json}"'
    else:
        python_exe = sys.executable
        app_path = BASE_DIR / "app.py"
        comando = f'"{python_exe}" "{app_path}" --auto "{test_json}"'
    
    with open(test_bat, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("chcp 65001 > nul\n")
        f.write(f'echo ============================================ > "{test_log}"\n')
        f.write(f'echo TESTE MANUAL - {datetime.now()} >> "{test_log}"\n')
        f.write(f'echo ============================================ >> "{test_log}"\n')
        f.write(f'echo. >> "{test_log}"\n')
        f.write(f'echo Executando comando: >> "{test_log}"\n')
        f.write(f'echo {comando} >> "{test_log}"\n')
        f.write(f'echo. >> "{test_log}"\n')
        f.write(f'{comando} >> "{test_log}" 2>&1\n')
        f.write(f'echo. >> "{test_log}"\n')
        f.write(f'echo Codigo de saida: %ERRORLEVEL% >> "{test_log}"\n')
        f.write(f'echo ============================================ >> "{test_log}"\n')
        f.write('pause\n')
    
    print(f"✓ BAT criado: {test_bat}")
    print(f"  Comando: {comando}")
    print(f"  Log: {test_log}")
    
    return test_bat, test_log


def test_3_executar_bat(bat_path, log_path):
    """Teste 3: Executar BAT manualmente"""
    print("\n" + "="*60)
    print("TESTE 3: Executando BAT manualmente")
    print("="*60)
    
    print(f"\n🔄 Executando: {bat_path}")
    print("   (Uma janela CMD vai abrir...)")
    
    try:
        # Executa o BAT e aguarda
        result = subprocess.run(
            [str(bat_path)],
            shell=True,
            cwd=str(BASE_DIR)
        )
        
        print(f"\n✓ BAT executado (código: {result.returncode})")
        
        # Mostra o log
        if log_path.exists():
            print(f"\n📋 Conteúdo do log ({log_path}):")
            print("-" * 60)
            with open(log_path, "r", encoding="utf-8") as f:
                print(f.read())
            print("-" * 60)
        else:
            print(f"\n⚠️  Log não foi criado: {log_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro ao executar BAT: {e}")
        return False


def test_4_criar_tarefa_windows():
    """Teste 4: Criar tarefa no Windows (2 minutos)"""
    print("\n" + "="*60)
    print("TESTE 4: Criando tarefa no Task Scheduler")
    print("="*60)
    
    # Cria para daqui a 2 minutos
    scheduled_time = datetime.now() + timedelta(minutes=2)
    run_date = scheduled_time.strftime("%d/%m/%Y")
    run_time = scheduled_time.strftime("%H:%M")
    
    test_bat = TASKS_DIR / "test_manual.bat"
    task_name = "StudyPractices_TEST_MANUAL"
    
    command = [
        "schtasks",
        "/Create",
        "/F",
        "/SC", "ONCE",
        "/SD", run_date,
        "/ST", run_time,
        "/TN", task_name,
        "/TR", f'"{test_bat}"',
        "/RL", "HIGHEST"
    ]
    
    print(f"📅 Agendando para: {scheduled_time.strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"   (daqui a 2 minutos)")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='latin-1'
        )
        
        print(f"\n✓ Tarefa criada: {task_name}")
        print(f"\n📌 Para testar AGORA (sem esperar):")
        print(f'   schtasks /Run /TN "{task_name}"')
        print(f"\n📋 Para ver detalhes:")
        print(f'   schtasks /Query /TN "{task_name}" /V /FO LIST')
        print(f"\n🗑️  Para deletar depois:")
        print(f'   schtasks /Delete /TN "{task_name}" /F')
        
        return task_name
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao criar tarefa:")
        print(f"   Código: {e.returncode}")
        if e.stdout:
            print(f"   Saída: {e.stdout}")
        if e.stderr:
            print(f"   Erro: {e.stderr}")
        return None


def test_5_executar_tarefa(task_name):
    """Teste 5: Forçar execução da tarefa"""
    print("\n" + "="*60)
    print("TESTE 5: Forçando execução da tarefa")
    print("="*60)
    
    command = [
        "schtasks",
        "/Run",
        "/TN", task_name
    ]
    
    print(f"🚀 Executando tarefa: {task_name}")
    
    try:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='latin-1'
        )
        
        print(f"✓ Tarefa iniciada!")
        print(f"\n⏳ Aguarde 10 segundos para a execução...")
        
        import time
        time.sleep(10)
        
        # Verifica log
        test_log = LOGS_DIR / "test_manual.log"
        if test_log.exists():
            print(f"\n📋 Log gerado ({test_log}):")
            print("-" * 60)
            with open(test_log, "r", encoding="utf-8") as f:
                print(f.read())
            print("-" * 60)
        else:
            print(f"\n⚠️  Log NÃO foi gerado: {test_log}")
            print("   Isso significa que o BAT não foi executado!")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao executar tarefa:")
        if e.stderr:
            print(f"   {e.stderr}")
        return False


def test_6_verificar_historico(task_name):
    """Teste 6: Verificar histórico da tarefa"""
    print("\n" + "="*60)
    print("TESTE 6: Verificando histórico de execução")
    print("="*60)
    
    command = [
        "schtasks",
        "/Query",
        "/TN", task_name,
        "/V",
        "/FO", "LIST"
    ]
    
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='latin-1'
        )
        
        print("📊 Informações da tarefa:")
        print("-" * 60)
        
        # Filtra linhas importantes
        for line in result.stdout.split('\n'):
            if any(keyword in line for keyword in [
                'Status:', 'Estado:',
                'Last Run Time:', 'Última Execução:',
                'Last Result:', 'Último Resultado:',
                'Next Run Time:', 'Próxima Execução:',
                'Task To Run:', 'Tarefa a Executar:'
            ]):
                print(line.strip())
        
        print("-" * 60)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao consultar tarefa: {e.stderr if e.stderr else 'Desconhecido'}")
        return False


# =============================
# MENU PRINCIPAL
# =============================

def main():
    print("\n" + "="*60)
    print("DIAGNÓSTICO DE AGENDAMENTO - Study Practices")
    print("="*60)
    print(f"\nDiretório base: {BASE_DIR}")
    print(f"Modo: {'EXE (compilado)' if getattr(sys, 'frozen', False) else 'Python (desenvolvimento)'}")
    
    while True:
        print("\n" + "="*60)
        print("MENU DE TESTES")
        print("="*60)
        print("1. Teste Completo (todos os passos)")
        print("2. Teste 1: Criar JSON")
        print("3. Teste 2: Criar BAT")
        print("4. Teste 3: Executar BAT manualmente")
        print("5. Teste 4: Criar tarefa no Windows")
        print("6. Teste 5: Forçar execução da tarefa")
        print("7. Teste 6: Ver histórico da tarefa")
        print("8. Limpar arquivos de teste")
        print("0. Sair")
        print("="*60)
        
        choice = input("\nEscolha uma opção: ").strip()
        
        if choice == "0":
            print("\n Encerrando...")
            break
        
        elif choice == "1":
            print("\n INICIANDO TESTE COMPLETO")
            test_json = test_1_criar_json()
            test_bat, test_log = test_2_criar_bat()
            test_3_executar_bat(test_bat, test_log)
            
            continuar = input("\n✓ Teste manual OK. Criar tarefa no Windows? (s/n): ")
            if continuar.lower() == 's':
                task_name = test_4_criar_tarefa_windows()
                if task_name:
                    executar = input("\n✓ Tarefa criada. Forçar execução agora? (s/n): ")
                    if executar.lower() == 's':
                        test_5_executar_tarefa(task_name)
                        test_6_verificar_historico(task_name)
        
        elif choice == "2":
            test_1_criar_json()
        
        elif choice == "3":
            test_2_criar_bat()
        
        elif choice == "4":
            test_bat = TASKS_DIR / "test_manual.bat"
            test_log = LOGS_DIR / "test_manual.log"
            if test_bat.exists():
                test_3_executar_bat(test_bat, test_log)
            else:
                print("❌ BAT não encontrado. Execute o Teste 2 primeiro.")
        
        elif choice == "5":
            test_4_criar_tarefa_windows()
        
        elif choice == "6":
            task_name = "StudyPractices_TEST_MANUAL"
            test_5_executar_tarefa(task_name)
        
        elif choice == "7":
            task_name = "StudyPractices_TEST_MANUAL"
            test_6_verificar_historico(task_name)
        
        elif choice == "8":
            print("\n🧹 Limpando arquivos de teste...")
            
            # Remove arquivos
            for file in [
                TASKS_DIR / "test_manual.json",
                TASKS_DIR / "test_manual.bat",
                LOGS_DIR / "test_manual.log"
            ]:
                if file.exists():
                    file.unlink()
                    print(f"  ✓ Removido: {file}")
            
            # Remove tarefa do Windows
            try:
                subprocess.run(
                    ["schtasks", "/Delete", "/TN", "StudyPractices_TEST_MANUAL", "/F"],
                    capture_output=True
                )
                print("  ✓ Tarefa do Windows removida")
            except:
                pass
            
            print("✓ Limpeza concluída!")
        
        else:
            print("❌ Opção inválida!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n Interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()