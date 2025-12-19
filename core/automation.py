import os
import time
import traceback

import undetected_chromedriver as uc

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


# Delays (ajustáveis)
WHATSAPP_LOAD = 10
SHORT_DELAY = 1.0
MID_DELAY = 1.6
LONG_DELAY = 2.0

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
        # fallback simples para stdout
        print(msg)

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
    candidates: [(By.XPATH, '...'), (By.CSS_SELECTOR, '...'), ...]
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
# Driver
# --------------------------
def iniciar_driver(userdir=None, headless=False, timeout=60, logger=None):
    """
    Inicia undetected_chromedriver com perfil persistente.
    Retorna driver pronto com WhatsApp Web aberto (ou pronto para autenticação).
    """
    try:
        if userdir is None:
            userdir = os.path.join(os.getcwd(), "chrome_profile")
        if not os.path.exists(userdir):
            os.makedirs(userdir)

        _log(logger, f"Iniciando Chrome com profile: {userdir}")

        options = uc.ChromeOptions()
        options.add_argument(f"--user-data-dir={userdir}")
        options.add_argument("--disable-notifications")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        if headless:
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")

        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(timeout)
        driver.maximize_window()

        _log(logger, "Chrome iniciado. Acessando WhatsApp Web...")
        driver.get("https://web.whatsapp.com")
        time.sleep(WHATSAPP_LOAD)

        # tentativa de confirmar painel lateral carregado (não fatal)
        try:
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "side")))
        except Exception:
            _log(logger, "Atenção: painel lateral não detectado — verifique se precisa escanear QR.")

        _log(logger, "WhatsApp Web carregado (ou pronto para autenticação manual).")
        return driver
    except Exception as e:
        _log(logger, f"Erro iniciar_driver: {e}")
        _log(logger, traceback.format_exc())
        raise

# --------------------------
# Buscar contato / abrir chat
# --------------------------
def procurar_contato_grupo(driver, target, logger=None, timeout=3):
    """
    Busca e abre a conversa com o contato/grupo pelo nome exato.
    Tenta vários seletores da caixa de busca; se falhar tenta clicar primeiro chat.
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
            # fallback: abrir primeiro chat da lista
            first_chat = _wait_clickable(driver, By.CSS_SELECTOR, "div[role='listitem']", timeout=3)
            if first_chat:
                try:
                    first_chat.click()
                    _log(logger, "Primeiro chat aberto como fallback (não pesquisado).")
                    return True
                except Exception:
                    pass
            raise Exception("Caixa de pesquisa não encontrada (XPaths testados).")

        # focar, limpar e digitar
        try:
            search_box.click()
        except Exception:
            driver.execute_script("arguments[0].focus();", search_box)
        time.sleep(0.2)
        try:
            # limpar (Ctrl+A + Del)
            search_box.send_keys(Keys.CONTROL + "a")
            search_box.send_keys(Keys.DELETE)
        except Exception:
            # fallback: executar script para limpar
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

        # tentar clicar no botão de enviar (setinha) primeiro; se não, enviar Enter
        send_btn = _wait(driver, By.XPATH, "//span[@data-icon='wds-ic-send-filled']", timeout=2)
        if not send_btn:
            send_btn = _wait(driver, By.CSS_SELECTOR, "span[data-icon='send']", timeout=2)
        if not send_btn:
            logger_msg = "Botão de enviar não encontrado; enviando com Enter."
            _log(logger, logger_msg)
            raise Exception(logger_msg)
            try:
                send_btn.click()
            except Exception as e:
                msg_box.send_keys(Keys.ENTER)
        else:
            msg_box.send_keys(Keys.ENTER)

        time.sleep(SHORT_DELAY)
        _log(logger, "Mensagem enviada.")
        return True
    except Exception as e:
        _log(logger, f"Erro enviar_mensagem_simples: {str(e)}")
        _log(logger, traceback.format_exc())
        raise

# --------------------------
# Funções de anexos / upload
# --------------------------
def clicar_clip(driver, logger=None):
    """
    Clica no botão de anexar (clip). Usa seletor baseado em data-icon ou fallback por role.
    """
    candidates = [
        (By.XPATH, "//span[@data-icon='plus-rounded']"),
        (By.CSS_SELECTOR, "button[aria-label='Anexar']"),
        (By.CSS_SELECTOR, "span[data-icon='plus-rounded']"),
    ]
    el, sel = _find(driver, candidates)
    if not el:
        raise Exception("Botão de anexar (clip) não encontrado.")
    try:
        el.click()
    except Exception:
        driver.execute_script("arguments[0].click();", el)
    time.sleep(0.6)
    _log(None, f"clicar_clip: clique realizado ({sel}).")
    return True

def clicar_botao_documento(driver, logger=None):
    """
    Clica na opção 'Documento' dentro do painel de anexos.
    Usa o texto visível 'Documento' como referência (mais estável).
    """
    # tenta localizar span com texto "Documento" e subir para o pai clicável
    try:
        el = _wait(driver, By.XPATH, "//span[normalize-space()='Documento']/parent::div", timeout=3)
        if not el:
            # fallback: localizar elemento pelo title/text parcial
            el = _wait(driver, By.XPATH, "//*[normalize-space()='Documento']", timeout=2)
            if el:
                el = el.find_element(By.XPATH, "./ancestor::div[1]")
        if not el:
            raise Exception("Botão 'Documento' não encontrado no painel de anexos.")
        try:
            el.click()
        except Exception:
            driver.execute_script("arguments[0].click();", el)
        time.sleep(0.5)
        _log(logger, "Opção 'Documento' clicada.")
        return True
    except Exception as e:
        _log(logger, f"Erro clicar_botao_documento: {e}")
        raise

def localizar_input_file(driver, logger=None, timeout=2.5):
    """
    Retorna o input[type='file'] mais provável (último no DOM), que é o que o WhatsApp usa.
    """
    try:
        # procura por inputs do tipo file e retorna o último
        els = driver.find_elements(By.XPATH, "//input[@type='file']")
        if not els:
            # fallback por css
            els = driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
        if not els:
            return None
        # escolher o último criado
        input_file = els[-1]
        return input_file
    except Exception as e:
        _log(logger, f"Erro localizar_input_file: {e}")
        return None

def upload_arquivo(driver, file_path, logger=None, timeout=6.3):
    """
    Envia caminho ao input[type=file].
    """
    try:
        input_file = localizar_input_file(driver, logger=logger, timeout=timeout)
        if not input_file:
            raise Exception("input[type='file'] não encontrado (após abrir painel).")
        # send_keys com caminho absoluto
        input_file.send_keys(file_path)
        time.sleep(1.2)  # dar tempo para o preview ser processado
        _log(logger, f"upload_arquivo: arquivo enviado ao input ({file_path}).")
        return True
    except Exception as e:
        _log(logger, f"Erro upload_arquivo: {e}")
        _log(logger, traceback.format_exc())
        raise

def clicar_enviar_arquivo(driver, logger=None, timeout=6.7):
    """
    Clica no botão verde de enviar arquivo (preview).
    """
    try:
        # Tentativa direta: botão com aria-label="Enviar"
        send_btn = _wait(driver, By.XPATH, "//div[@role='button' and @aria-label='Enviar']", timeout=5)
        if not send_btn:
            # fallback: span com ícone de send dentro do preview
            send_btn = _wait(driver, By.XPATH, "//span[@data-icon='wds-ic-send-filled' or @data-icon='send']", timeout=5)
        if not send_btn:
            # fallback: botão verde genérico
            send_btn = _wait(driver, By.CSS_SELECTOR, "button[aria-label='Enviar']", timeout=5)
        if not send_btn:
            raise Exception("Botão para confirmar envio do arquivo não encontrado.")
        try:
            send_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", send_btn)
        time.sleep(1.0)
        _log(logger, "clicar_enviar_arquivo: clique realizado.")
        return True
    except Exception as e:
        _log(logger, f"Erro clicar_enviar_arquivo: {e}")
        _log(logger, traceback.format_exc())
        raise

# --------------------------
# Funções públicas de envio
# --------------------------
def enviar_arquivo(driver, file_path, logger=None):
    """
    Envia apenas o arquivo (sem legenda).
    Fluxo:
    - clicar clip
    - clicar Documento (ou outra opção necessária)
    - localizar input[type=file] e enviar caminho
    - clicar botão de enviar do preview
    """
    try:
        _log(logger, f"Anexando arquivo: {file_path}")

        clicar_clip(driver, logger=logger)

        try:
            clicar_botao_documento(driver, logger=logger)
        except Exception:
            _log(logger, "Opção 'Documento' não encontrada — tentando upload pelo input")

        # upload do arquivo
        input_file = localizar_input_file(driver, logger)
        if not input_file:
            raise Exception("input[type='file'] não encontrado para upload do arquivo")

        input_file.send_keys(file_path)
        time.sleep(1.2)

        # encontrar o botão de enviar arquivo
        send_btn = _wait(driver, By.XPATH, "//div[@role='button' and @aria-label='Enviar']", timeout=8)
        if not send_btn:
            send_btn = _wait(driver, By.XPATH, "//span[@data-icon='wds-ic-send-filled' or @data-icon='send']", timeout=8)

        if not send_btn:
            raise Exception("Botão de envio do arquivo não encontrado")

        try:
            send_btn.click()
        except Exception as e:
            _log(logger, "Falha ao clicar botão de enviar arquivo")
            raise e

        _log(logger, "Arquivo enviado com sucesso")
        return True

    except Exception as e:
        _log(logger, f"Erro enviar_arquivo: {e}")
        raise
    time.sleep(2)

def enviar_arquivo_com_mensagem(driver, file_path, message, logger=None):
    """
    Envia arquivo com legenda (mensagem).
    Observação: alguns campos de legenda só aparecem após upload; usamos espera.
    """
    try:
        _log(logger, f"Anexando arquivo com legenda: {file_path}")

        clicar_clip(driver, logger=logger)

        try:
            clicar_botao_documento(driver, logger=logger)
        except Exception:
            _log(logger, "Documento não obrigatório — seguindo")

        input_file = localizar_input_file(driver, logger)
        if not input_file:
            raise Exception("Não foi possível localizar input[type='file']")

        input_file.send_keys(file_path)
        time.sleep(1.0)

        caption_candidates = [
            (By.XPATH, "//div[@role='textbox' and @aria-label='Digite uma mensagem']"),
            (By.XPATH, "//div[@contenteditable='true' and @data-tab='6']"),
            (By.CSS_SELECTOR, "div[contenteditable='true']")
        ]

        caption_box, sel = _find(driver, caption_candidates)
        if not caption_box:
            _log(logger, "Caixa de legenda não encontrada — ignorando legenda")
        else:
            try:
                caption_box.click()
                if message:
                    caption_box.send_keys(message)
                    time.sleep(0.4)
            except Exception as e:
                raise Exception("Falha ao inserir legenda")

        send_btn = _wait(driver, By.XPATH, "//div[@role='button' and @aria-label='Enviar']", timeout=8)
        if not send_btn:
            send_btn = _wait(driver, By.XPATH, "//span[@data-icon='wds-ic-send-filled' or @data-icon='send']", timeout=8)

        if not send_btn:
            raise Exception("Botão de envio do arquivo+mensagem não encontrado")

        try:
            send_btn.click()
        except Exception as e:
            _log(logger, "Falha ao clicar botão de envio de arquivo + mensagem")
            raise e

        _log(logger, "Arquivo + mensagem enviados com sucesso")
        return True

    except Exception as e:
        _log(logger, f"Erro enviar_arquivo_com_mensagem: {e}")
        raise
    time.sleep(3)

# --------------------------
# Função mestre
# --------------------------
def executar_envio(userdir, target, mode, message=None, file_path=None, logger=None):
    """
    Função mestre: inicializa driver, procura contato e decide qual envio executar.
    mode: 'text', 'file', 'file_text'
    """
    driver = None
    try:
        driver = iniciar_driver(userdir=userdir, headless=False, logger=logger)
        procurar_contato_grupo(driver, target, logger=logger)
        time.sleep(1.0)

        if mode == "text":
            if not message:
                raise Exception("Modo 'text' selecionado mas nenhuma mensagem fornecida.")
            enviar_mensagem_simples(driver, message, logger=logger)
        elif mode == "file":
            if not file_path:
                raise Exception("Modo 'file' selecionado mas nenhum arquivo fornecido.")
            enviar_arquivo(driver, file_path, logger=logger)
        elif mode == "file_text":
            if not file_path:
                raise Exception("Arquivo necessário para modo 'file_text'.")
            enviar_arquivo_com_mensagem(driver, file_path, message or "", logger=logger)
        else:
            raise Exception("Modo desconhecido.")
        return True
    except Exception as e:
        _log(logger, f"Erro em executar_envio: {str(e)}")
        _log(logger, traceback.format_exc())
        raise
    finally:
        if driver:
            try:
                time.sleep(5)
                driver.quit()
                _log(logger, "Driver finalizado.")
            except Exception:
                pass
