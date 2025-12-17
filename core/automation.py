import os
import time
import traceback
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


# =====================================================
# UTIL
# =====================================================
def _log(logger, msg):
    """Logger unificado que aceita função ou objeto logger"""
    if logger:
        if callable(logger):
            # Se for função (como no modo auto)
            logger(msg)
        elif hasattr(logger, 'info'):
            # Se for objeto logger (como logging.Logger)
            logger.info(msg)
        else:
            print(msg)
    else:
        print(msg)


# =====================================================
# DRIVER
# =====================================================
def iniciar_driver(userdir, headless=False, logger=None):
    options = uc.ChromeOptions()

    if userdir:
        options.add_argument(f"--user-data-dir={userdir}")
    
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-extensions")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")

    _log(logger, f"Iniciando Chrome | headless={headless} | userdir={userdir}")
    
    try:
        driver = uc.Chrome(options=options, version_main=None)
        driver.get("https://web.whatsapp.com")
        return driver
    except Exception as e:
        _log(logger, f"ERRO ao iniciar driver: {e}")
        raise


# =====================================================
# VERIFICA LOGIN
# =====================================================
def verificar_whatsapp_logado(driver, timeout=30):
    """Verifica se WhatsApp Web está logado"""
    try:
        _log(None, f"Aguardando login do WhatsApp (timeout: {timeout}s)...")
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[@id='pane-side']")
            )
        )
        _log(None, "WhatsApp Web logado com sucesso!")
        return True
    except Exception as e:
        _log(None, f"WhatsApp Web não está logado: {e}")
        return False


# =====================================================
# MODO LOGIN (MANUAL)
# =====================================================
def modo_login(userdir, logger=None):
    """
    Abre WhatsApp Web SOMENTE para login manual.
    Não executa envio.
    Mantém navegador aberto.
    """

    driver = iniciar_driver(
        userdir=userdir,
        headless=False,
        logger=logger
    )

    _log(logger, "===================================")
    _log(logger, "MODO LOGIN ATIVO")
    _log(logger, "Escaneie o QR Code se necessário.")
    _log(logger, "Após confirmar o login, FECHE O CHROME MANUALMENTE.")
    _log(logger, "===================================")

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        _log(logger, "Login interrompido pelo usuário")
        if driver:
            driver.quit()


# =====================================================
# EXECUÇÃO DE ENVIO (AUTOMÁTICO)
# =====================================================
def executar_envio(
    userdir,
    target,
    mode,
    message=None,
    file_path=None,
    logger=None,
    headless=True
):
    """
    Executa o envio de mensagem/arquivo via WhatsApp Web
    
    Args:
        userdir: Diretório do perfil do Chrome
        target: Nome do contato ou número com código do país
        mode: 'text', 'file' ou 'file_text'
        message: Texto da mensagem (obrigatório para text/file_text)
        file_path: Caminho do arquivo (obrigatório para file/file_text)
        logger: Função ou objeto para logging
        headless: Se True, executa sem interface gráfica
    """
    driver = None

    try:
        _log(logger, "=" * 60)
        _log(logger, "INICIANDO EXECUÇÃO DE ENVIO")
        _log(logger, f"Target: {target}")
        _log(logger, f"Mode: {mode}")
        _log(logger, f"Headless: {headless}")
        _log(logger, "=" * 60)

        # Inicia driver
        driver = iniciar_driver(
            userdir=userdir,
            headless=headless,
            logger=logger
        )

        _log(logger, "Verificando sessão do WhatsApp Web...")

        if not verificar_whatsapp_logado(driver, timeout=40):
            raise Exception(
                "WhatsApp Web NÃO está logado. "
                "Execute o aplicativo em modo normal primeiro para fazer login."
            )

        _log(logger, "WhatsApp Web autenticado com sucesso.")

        # =============================
        # ABRIR CONVERSA
        # =============================
        _log(logger, f"Abrindo conversa com: {target}")
        
        # Tenta diferentes formatos de URL
        if target.isdigit():
            # Se for número puro, usa API do WhatsApp
            driver.get(f"https://web.whatsapp.com/send?phone={target}")
        else:
            # Se for nome, busca na lista de conversas
            driver.get("https://web.whatsapp.com")
            time.sleep(3)
            
            # Busca o contato
            search_box = WebDriverWait(driver, 6).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//div[@contenteditable='true'][@data-tab='3']")
                )
            )
            search_box.click()
            search_box.send_keys(target)
            time.sleep(2)
            
            # Clica no primeiro resultado
            contact = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable(
                    (By.XPATH, f"//span[@title='{target}']")
                )
            )
            contact.click()

        # Aguarda caixa de mensagem aparecer
        _log(logger, "Aguardando caixa de mensagem...")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//footer//div[@contenteditable='true']")
            )
        )
        
        time.sleep(2)  # Aguarda carregamento completo

        # =============================
        # ENVIO TEXTO
        # =============================
        if mode in ("text", "file_text"):
            if not message:
                raise ValueError("Mensagem não pode estar vazia para modo text/file_text")
            
            _log(logger, "Digitando mensagem...")
            caixa = driver.find_element(By.XPATH, "//footer//div[@contenteditable='true']")
            caixa.click()
            time.sleep(0.5)
            
            # Divide mensagem em linhas se tiver quebras
            linhas = message.split('\n')
            for i, linha in enumerate(linhas):
                caixa.send_keys(linha)
                if i < len(linhas) - 1:
                    # Shift+Enter para nova linha
                    from selenium.webdriver.common.keys import Keys
                    caixa.send_keys(Keys.SHIFT, Keys.ENTER)
            
            if mode == "text":
                # Envia mensagem
                _log(logger, "Enviando mensagem...")
                caixa.send_keys("\n")
                time.sleep(2)

        # =============================
        # ENVIO ARQUIVO
        # =============================
        if mode in ("file", "file_text"):
            if not file_path or not os.path.exists(file_path):
                raise ValueError(f"Arquivo não encontrado: {file_path}")
            
            _log(logger, f"Anexando arquivo: {file_path}")
            
            # Clica no botão de anexo
            attach = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//div[@title='Anexar']")
                )
            )
            attach.click()
            time.sleep(1)
            
            # Localiza input file
            input_file = driver.find_element(
                By.XPATH,
                "//input[@accept='*'][@type='file']"
            )
            input_file.send_keys(os.path.abspath(file_path))
            
            _log(logger, "Aguardando preview do arquivo...")
            time.sleep(3)
            
            # Se for file_text, adiciona legenda
            if mode == "file_text" and message:
                try:
                    caption_box = driver.find_element(
                        By.XPATH,
                        "//div[@contenteditable='true'][@data-tab='10']"
                    )
                    caption_box.click()
                    caption_box.send_keys(message)
                    time.sleep(1)
                except Exception as e:
                    _log(logger, f"Aviso: Não foi possível adicionar legenda: {e}")
            
            # Clica no botão de enviar
            _log(logger, "Enviando arquivo...")
            send_btn = WebDriverWait(driver, 60).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//span[@data-icon='send']")
                )
            )
            send_btn.click()
            
            # Aguarda envio completar
            time.sleep(5)

        _log(logger, "✓ Envio realizado com sucesso!")
        time.sleep(2)

    except Exception as e:
        _log(logger, f"✗ Erro durante execução do envio: {e}")
        _log(logger, traceback.format_exc())
        raise

    finally:
        if driver:
            _log(logger, "Encerrando navegador...")
            try:
                driver.quit()
            except:
                pass
            _log(logger, "=" * 60)