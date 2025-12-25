import os
import time
import traceback
import sys
import undetected_chromedriver as uc
import json
import shutil
import tempfile
import uuid
import random
import subprocess
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Delays (ajustáveis)
WHATSAPP_LOAD = 10
SHORT_DELAY = 1.0
MID_DELAY = 1.6
LONG_DELAY = 2.0

# --- FUNÇÃO PARA AGENDAMENTO ---
def run_auto(json_path):
    """ Função chamada pelo app.py quando o Windows dispara o agendamento. Lê o arquivo JSON e executa a automação. """
    print(f"Iniciando automação agendada: {json_path}")
    
    if not os.path.exists(json_path):
        print(f"Erro: Arquivo {json_path} não encontrado.")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            dados = json.load(f)
        
        # Extrai os dados do JSON gerado pela sua interface
        target = dados.get("target")
        mode = dados.get("mode")
        message = dados.get("message")
        file_path = dados.get("file_path")

        # CORREÇÃO: Passa is_scheduled=True para indicar execução agendada
        executar_envio(
            userdir=None,
            target=target,
            mode=mode,
            message=message,
            file_path=file_path,
            logger=lambda m: print(f"[AUTO-LOG] {m}"),
            is_scheduled=True  # NOVO: Indica que é execução agendada
        )
        print("✓ Automação agendada concluída com sucesso.")
        
    except Exception as e:
        print(f"❌ Erro na execução automática: {e}")
        traceback.print_exc()
        sys.exit(1)

# --------------------------
# Utilitários internos
# --------------------------
def _log(logger, msg):
    """Log centralizado: usa callable logger se fornecido"""
    if logger:
        try:
            logger(msg)
        except Exception:
            pass
    else:
        print(msg)

def criar_perfil_temporario(base_profile_dir, logger=None):
    try:
        temp_dir = os.path.join(tempfile.gettempdir(), f"whatsapp_bot_profile_{uuid.uuid4().hex[:8]}")
        _log(logger, f"Clonando perfil para uso paralelo: {temp_dir}")
        
        def copy_with_ignore(src, dst):
            try:
                shutil.copy2(src, dst)
            except Exception:
                pass

        shutil.copytree(base_profile_dir, temp_dir, dirs_exist_ok=True, copy_function=copy_with_ignore)
        
        return temp_dir
    except Exception as e:
        _log(logger, f"Erro crítico ao clonar: {e}. Tentando seguir com original.")
        return base_profile_dir

def _wait(driver, by, selector, timeout=10):
    """Espera por presença de elemento e retorna WebElement ou None."""
    try:
        return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, selector)))
    except Exception:
        return None

def _wait_clickable(driver, by, selector, timeout=10):
    """Espera por elemento clicável."""
    try:
        return WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, selector)))
    except Exception:
        return None

def _find(driver, candidates):
    """
    Recebe lista de tuplas (By, selector) e retorna o primeiro WebElement encontrado.
    """
    for by, sel in candidates:
        try:
            el = _wait(driver, by, sel, timeout=6)
            if el:
                return el, (by, sel)
        except Exception:
            continue
    return None, None

# --------------------------
# Headless a partir da 3ª execução
# --------------------------
def contador_execucao(incrementar=True):
    import sys
    import os

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    count_file = os.path.join(base_dir, "execution_count.txt")
    
    count = 0
    if os.path.exists(count_file):
        try:
            with open(count_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                count = int(content) if content else 0
        except Exception as e:
            print(f"Erro ao ler arquivo de contagem: {e}")
            count = 0

    if incrementar:
        count += 1
        try:
            with open(count_file, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(str(count))
                f.flush()
                os.fsync(f.fileno()) 
        except Exception as e:
            print(f"Erro ao gravar contador: {e}")
            
    return count

# --------------------------
# Driver
# --------------------------
def iniciar_driver(userdir=None, headless=False, timeout=60, logger=None):
    """
    Inicia o undetected_chromedriver.
    CORREÇÃO: Agora respeita o parâmetro headless corretamente.
    """
    import os, sys, time, random
    import undetected_chromedriver as uc
    driver = None

    try:
        if userdir is None:
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                base_dir = os.path.join(base_dir, "..")
            userdir = os.path.join(base_dir, "perfil_bot_whatsapp")
        
        if not os.path.exists(userdir):
            os.makedirs(userdir)
            if logger: logger(f"Criado perfil em: {userdir}")

        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={userdir}")
        
        # Configurações básicas (sempre)
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--no-first-run')
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-default-browser-check")
        options.add_argument("--disable-session-crashed-bubble")
        options.add_argument("--disable-notifications")
        
        # CORREÇÃO: Configurações específicas por modo
        if headless:
            if logger: logger("Iniciando Chrome em modo HEADLESS (invisível)...")
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--window-size=1920,1080')
            debug_port = random.randint(9000, 9999)
            options.add_argument(f'--remote-debugging-port={debug_port}')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        else:
            if logger: logger("Iniciando Chrome em modo VISÍVEL...")
            options.add_argument("--start-maximized")
        
        # Inicia o driver
        driver = uc.Chrome(
            options=options,
            use_subprocess=False,  # CORREÇÃO: False para evitar problemas de processo
            version_main=None
        )
        
        if logger: logger("✓ Chrome iniciado com sucesso")
        
        # Ajusta janela conforme o modo
        if headless:
            driver.set_window_size(1920, 1080)
        else:
            try:
                driver.maximize_window()
            except:
                driver.set_window_size(1920, 1080)

        driver.set_page_load_timeout(timeout)

        # Acessa WhatsApp Web
        if logger: logger("Acessando WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        
        # Tempo de carregamento adaptativo
        tempo_espera = 25 if headless else 15
        if logger: logger(f"Aguardando {tempo_espera}s para WhatsApp carregar...")
        time.sleep(tempo_espera)
        
        if logger: logger("✓ WhatsApp Web carregado")
        return driver

    except Exception as e:
        if logger: logger(f"❌ ERRO ao iniciar driver: {str(e)}")
        if driver is not None:
            try: 
                driver.quit()
            except: 
                pass
        raise

# --------------------------
# Buscar contato / abrir chat
# --------------------------
def procurar_contato_grupo(driver, target, logger=None, timeout=2):
    """
    Busca e abre a conversa com o contato/grupo pelo nome exato.
    MANTIDO: XPaths originais preservados.
    """
    try:
        _log(logger, f"Procurando contato/grupo: {target}")

        search_candidates = [
            (By.XPATH, "//div[@contenteditable='true' and (@data-tab='3' or @data-tab='1')]"),
            (By.XPATH, "//div[contains(@aria-label,'Pesquisar') or contains(@aria-label,'Pesquisar ou começar')]"),
            (By.CSS_SELECTOR, "div[contenteditable='true'][data-tab]"),
        ]

        search_box, sel = _find(driver, search_candidates)
        if not search_box:
            _log(logger, "Campo de busca não encontrado via seletores comuns. Tentando abrir primeiro chat como fallback...")
            first_chat = _wait_clickable(driver, By.CSS_SELECTOR, "div[role='listitem']", timeout=2)
            if first_chat:
                try:
                    first_chat.click()
                    _log(logger, "Primeiro chat aberto como fallback (não pesquisado).")
                    return True
                except Exception:
                    pass
            raise Exception("Caixa de pesquisa não encontrada (XPaths testados).")

        try:
            search_box.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", search_box)
        time.sleep(0.2)
        try:
            search_box.send_keys(Keys.CONTROL + "a")
            search_box.send_keys(Keys.DELETE)
        except Exception:
            driver.execute_script("arguments[0].innerText = '';", search_box)
        time.sleep(0.2)
        search_box.send_keys(target)
        time.sleep(SHORT_DELAY)
        search_box.send_keys(Keys.ENTER)
        time.sleep(MID_DELAY)

        _log(logger, "Contato/grupo aberto.")
        return True
    except Exception as e:
        _log(logger, f"Erro procurar_contato_grupo: {str(e)}")
        _log(logger, traceback.format_exc())
        raise

# --------------------------
# Mensagem de texto
# --------------------------
def enviar_mensagem_simples(driver, message, logger=None, timeout=4):
    """
    Envia apenas mensagem de texto no chat já aberto.
    MANTIDO: XPaths originais preservados.
    """
    try:
        _log(logger, "Enviando mensagem de texto...")
        msg_candidates = [
            (By.XPATH, "//div[@role='textbox' and @contenteditable='true' and @aria-label='Digite uma mensagem']"),
            (By.XPATH, "//div[@contenteditable='true' and (@data-tab='10' or @data-tab='6')]"),
            (By.CSS_SELECTOR, "footer div[contenteditable='true']"),
        ]
        msg_box, sel = _find(driver, msg_candidates)
        if not msg_box:
            raise Exception("Campo de mensagem não encontrado.")

        try:
            msg_box.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", msg_box)
        time.sleep(0.2)
        msg_box.send_keys(message)
        time.sleep(0.3)

        send_btn = _wait(driver, By.XPATH, "//span[@data-icon='wds-ic-send-filled']", timeout=2)
        if not send_btn:
            send_btn = _wait(driver, By.CSS_SELECTOR, "span[data-icon='send']", timeout=2)
        if not send_btn:
            logger_msg = "Botão de enviar não encontrado; enviando com Enter."
            _log(logger, logger_msg)
            msg_box.send_keys(Keys.ENTER)
        else:
            try:
                send_btn.click()
            except:
                msg_box.send_keys(Keys.ENTER)

        time.sleep(SHORT_DELAY)
        _log(logger, "Mensagem enviada.")
        return True
    except Exception as e:
        _log(logger, f"Erro enviar_mensagem_simples: {str(e)}")
        _log(logger, traceback.format_exc())
        raise

# --------------------------
# CORREÇÃO: Envio de arquivos (múltiplos)
# --------------------------
def enviar_arquivos(driver, file_paths, message=None, headless=False, logger=None):
    """
    NOVO: Envia um ou múltiplos arquivos com ou sem legenda.
    Usa apenas send_keys() no input[type='file'] - técnica oficial do Selenium.
    
    Args:
        file_paths: str (caminho único) ou list (múltiplos caminhos)
        message: legenda opcional
        headless: se True, usa técnica headless
    """
    try:
        # Converte string única para lista
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        
        # Valida que todos os arquivos existem
        for fp in file_paths:
            if not os.path.exists(fp):
                raise Exception(f"Arquivo não encontrado: {fp}")
        
        _log(logger, f"Anexando {len(file_paths)} arquivo(s)...")
        
        # 1. LOCALIZA O INPUT (sempre presente no DOM, mesmo invisível)
        input_file = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        
        # 2. ENVIA OS ARQUIVOS
        # Para múltiplos arquivos, concatena com \n (funciona no Chrome/Selenium)
        if len(file_paths) == 1:
            abs_path = os.path.abspath(file_paths[0])
            input_file.send_keys(abs_path)
            _log(logger, f"Arquivo enviado: {os.path.basename(abs_path)}")
        else:
            # Múltiplos arquivos: junta com newline
            abs_paths = [os.path.abspath(fp) for fp in file_paths]
            combined = "\n".join(abs_paths)
            input_file.send_keys(combined)
            _log(logger, f"{len(file_paths)} arquivos enviados")
        
        # 3. AGUARDA O PREVIEW CARREGAR
        wait_time = 8 if headless else 4
        _log(logger, f"Aguardando {wait_time}s para preview processar...")
        time.sleep(wait_time)
        
        # 4. VERIFICA SE O PREVIEW ABRIU
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//div[@role='button' and @aria-label='Enviar']"))
            )
            _log(logger, "✓ Preview detectado")
        except:
            raise Exception("Preview não abriu - WhatsApp pode não ter processado os arquivos")
        
        # 5. ADICIONA LEGENDA (SE FORNECIDA)
        if message:
            try:
                _log(logger, "Inserindo legenda...")
                caption_selectors = [
                    "//div[@role='textbox' and @aria-label='Adicionar legenda']",
                    "//div[@role='textbox' and @contenteditable='true' and @data-tab='10']",
                    "//div[@contenteditable='true' and contains(@class, 'copyable-text')]"
                ]
                
                caption_box = None
                for selector in caption_selectors:
                    try:
                        caption_box = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, selector))
                        )
                        if caption_box:
                            break
                    except:
                        continue
                
                if caption_box:
                    try:
                        caption_box.click()
                    except:
                        driver.execute_script("arguments[0].focus();", caption_box)
                    
                    time.sleep(0.5)
                    caption_box.send_keys(message)
                    _log(logger, f"✓ Legenda inserida: {message[:50]}...")
                    time.sleep(1)
                else:
                    _log(logger, "⚠️ Campo de legenda não encontrado")
            except Exception as e:
                _log(logger, f"⚠️ Erro ao inserir legenda: {e}")
        
        # 6. CLICA NO BOTÃO DE ENVIAR
        _log(logger, "Enviando arquivo(s)...")
        send_xpath = "//div[@role='button' and @aria-label='Enviar'] | //span[@data-icon='send'] | //span[@data-icon='wds-ic-send-filled']"
        send_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, send_xpath))
        )
        
        try:
            send_btn.click()
        except:
            driver.execute_script("arguments[0].click();", send_btn)
        
        _log(logger, "✓ Clique no botão realizado")
        
        # 7. AGUARDA CONFIRMAÇÃO REAL DE ENVIO
        _log(logger, "Aguardando confirmação (até 60s)...")
        preview_fechou = False
        try:
            WebDriverWait(driver, 60).until_not(
                EC.presence_of_element_located((By.XPATH, "//div[@role='button' and @aria-label='Enviar']"))
            )
            preview_fechou = True
            _log(logger, "✓ Preview fechado - arquivo(s) enviado(s)")
        except:
            _log(logger, "⚠️ Timeout aguardando preview fechar")
        
        if not preview_fechou:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@role='textbox' and @contenteditable='true']"))
                )
                _log(logger, "✓ Retornou à tela de chat")
            except:
                _log(logger, "⚠️ Não foi possível confirmar o envio")
        
        time.sleep(5)
        _log(logger, f"✓ {len(file_paths)} arquivo(s) enviado(s) com sucesso")
        return True
        
    except Exception as e:
        _log(logger, f"❌ Erro ao enviar arquivo(s): {e}")
        _log(logger, traceback.format_exc())
        raise

# --------------------------
# Função mestre (CORRIGIDA)
# --------------------------
def executar_envio(userdir, target, mode, message=None, file_path=None, logger=None, is_scheduled=False):
    """
    Função mestre: inicializa driver, procura contato e executa envio.
    
    CORREÇÃO PRINCIPAL:
    - Novo parâmetro is_scheduled para diferenciar contextos
    - Headless APENAS quando is_scheduled=True
    - Suporte a múltiplos arquivos via lista em file_path
    
    Args:
        userdir: diretório do perfil Chrome
        target: contato/número
        mode: 'text', 'file', 'file_text'
        message: texto da mensagem
        file_path: str (um arquivo) ou list (múltiplos arquivos)
        logger: função de log
        is_scheduled: True se execução é agendada (headless), False se manual (visível)
    """
    driver = None
    perfil_final = None

    try:
        # Define diretório base
        if userdir is None:
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            userdir = os.path.join(base_dir, "perfil_bot_whatsapp")

        # CORREÇÃO: Para execução manual, não clona perfil (evita problemas)
        if is_scheduled:
            # Apenas agendamentos usam perfil temporário
            perfil_final = criar_perfil_temporario(userdir, logger)
        else:
            # Execução manual usa perfil direto
            perfil_final = userdir
            _log(logger, f"Usando perfil direto: {perfil_final}")

        # CORREÇÃO: Headless APENAS se for execução agendada
        usar_headless = is_scheduled
        
        driver = iniciar_driver(userdir=perfil_final, headless=usar_headless, logger=logger)
        
        vezes_executadas = contador_execucao(incrementar=False)
        if logger:
            logger(f'Execução número {vezes_executadas}')
            logger(f'Modo: {"Headless (agendado)" if usar_headless else "Visível (manual)"}')

        # Procura contato
        procurar_contato_grupo(driver, target, logger=logger)
        time.sleep(2.0)

        # Executa o modo selecionado
        if mode == "text":
            if not message:
                raise Exception("Modo 'text' selecionado mas nenhuma mensagem fornecida.")
            enviar_mensagem_simples(driver, message, logger=logger)
            
        elif mode == "file":
            if not file_path:
                raise Exception("Modo 'file' selecionado mas nenhum arquivo fornecido.")
            # CORREÇÃO: Usa nova função que suporta múltiplos arquivos
            enviar_arquivos(driver, file_path, message=None, headless=usar_headless, logger=logger)
            
        elif mode == "file_text":
            if not file_path:
                raise Exception("Arquivo necessário para modo 'file_text'.")
            # CORREÇÃO: Usa nova função que suporta múltiplos arquivos + legenda
            enviar_arquivos(driver, file_path, message=message or "", headless=usar_headless, logger=logger)
            
        else:
            raise Exception("Modo desconhecido.")
        
        _log(logger, "Aguardando confirmação final...")
        time.sleep(8)
        
        _log(logger, "=" * 50)
        _log(logger, "✓✓✓ ENVIO CONCLUÍDO COM SUCESSO ✓✓✓")
        _log(logger, "=" * 50)
        
        return True
        
    except Exception as e:
        _log(logger, f"❌ Erro em executar_envio: {str(e)}")
        _log(logger, traceback.format_exc())
        raise
        
    finally:
        if driver:
            try:
                _log(logger, "Aguardando antes de fechar (10s)...")
                time.sleep(10)
                _log(logger, "Finalizando driver...")
                driver.quit()
                driver.close()
                _log(logger, "Driver finalizado.")
            except Exception as e:
                _log(logger, f"Erro ao fechar driver: {e}")
        
        # Remove perfil temporário APENAS se foi criado
        if perfil_final and perfil_final != userdir and is_scheduled:
            try:
                time.sleep(3)
                shutil.rmtree(perfil_final, ignore_errors=True)
                _log(logger, f"Perfil temporário removido: {perfil_final}")
            except Exception as e:
                _log(logger, f"Aviso: Não foi possível remover perfil temporário: {e}")