import pandas as pd
import numpy  as np
import time
import random
import os
import shutil
import psutil
import subprocess
import sys
from vpn                                            import VPNChanger
from config                                         import proxy_ip_port, proxy_user_pass
from loguru                                         import logger
from urllib.parse                                   import urlparse, urljoin
from selenium                                       import webdriver
from selenium.webdriver.chrome.service              import Service
from selenium.webdriver.chrome.options              import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy                import Proxy, ProxyType
from webdriver_manager.chrome import ChromeDriverManager  # Importação adicionada

# Configuração do logger
logger.remove()
logger.add(sys.stderr, level="DEBUG")  # Altere o nível conforme necessário

vpn_changer = VPNChanger()
vpn_files = vpn_changer.get_vpn_files()

class WebScraper:
    def __init__(self, chromedriver_path, user_agents, cache_path):
        self.chromedriver_path = chromedriver_path
        self.user_agents = user_agents
        self.cache_path = cache_path
        self.driver = None
        self.session_id = proxy_ip_port
        self.proxy_user_pass = proxy_user_pass


    def ensure_cache_path(self):
        logger.debug(f"Verificando se o caminho do cache existe: {self.cache_path}")
        if not os.path.exists(self.cache_path):
            os.makedirs(self.cache_path)
            logger.debug(f"Criado diretório de cache: {self.cache_path}")

    def header_configuration(self, headless=True):
        self.ensure_cache_path()
        webdriver_service = Service(self.chromedriver_path)

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
        chrome_options.add_argument(f'--user-data-dir={self.cache_path}')
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--remote-debugging-port=9222")           ## Limpou o erro do chrome teste, e conseguiu conectar finalmente FILA DA PUTA
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("window-size=1200x800")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-translate")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-autofill")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-animations")
        # chrome_options.add_argument("--disable-cache")
        chrome_options.binary_location = r'chrome-win64/chrome.exe'
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])

        # Desabilitar imagens e estilos para melhorar o desempenho
        prefs = {
            "profile.default_content_setting_values.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Configuração opcional de proxy
        proxy_options = {
            'proxy': {
                'http': f'https://{proxy_user_pass}@{proxy_ip_port}',
                'https': f'https://{proxy_user_pass}@{proxy_ip_port}',
                'no_proxy': 'localhost,127.0.0.1',
                'verify_ssl': False,
            }
        }

        self.driver = webdriver.Chrome(service=webdriver_service, options=chrome_options)
        # self.driver = webdriver.Chrome(service=webdriver_service, seleniumwire_options=proxy_options, options=chrome_options)

        return self.driver

    def delete_cache(self, get_previous_url=True):
        url_atual = None
        if get_previous_url and self.driver:
            try:
                url_atual = self.driver.current_url
            except Exception as e:
                logger.error(f"O driver já foi fechado. Erro: {e}")
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
        except Exception as e:
            logger.error(f"Não foi possível fechar o driver. Erro: {e}")
        if os.path.exists(self.cache_path):
            shutil.rmtree(self.cache_path)
            logger.debug("Cache deletado com sucesso!")
        if url_atual:
            self.driver = self.header_configuration()
            self.driver.get(url_atual)

    def scroll(self, element=None, start=0, end=3600, step=300, reverse=False):
        logger.debug(f"Iniciando scroll: start={start}, end={end}, step={step}, reverse={reverse}")
        if not element:
            element = self.driver.find_element_by_tag_name('body')

        def is_scrollable(element):
            scroll_height = element.get_attribute("scrollHeight")
            client_height = element.get_attribute("clientHeight")
            scrollable = int(scroll_height) > int(client_height)
            logger.debug(f"Verificação de rolagem: scrollHeight={scroll_height}, clientHeight={client_height}, scrollable={scrollable}")
            return scrollable

        if reverse:
            start, end = end, start
            step = -step

        if step == 0:
            logger.error("O valor de step não pode ser zero.")
            raise ValueError("Step não pode ser zero.")

        max_scroll_height = int(element.get_attribute("scrollHeight"))
        current_scroll_position = int(float(element.get_attribute("scrollTop")))
        logger.debug(f"Altura máxima de rolagem: {max_scroll_height}")
        logger.debug(f"Posição atual de rolagem: {current_scroll_position}")

        if reverse:
            if current_scroll_position < start:
                start = current_scroll_position
            logger.debug(f"Posição inicial ajustada para rolagem reversa: {start}")
        else:
            if end > max_scroll_height:
                logger.warning(f"O valor de end excede a altura de rolagem. Ajustando end para {max_scroll_height}")
                end = max_scroll_height

        script_scroll_to = "arguments[0].scrollTop = arguments[1];"

        try:
            if element.is_displayed():
                if not is_scrollable(element):
                    logger.warning("O elemento não é rolável.")
                    return

                if (step > 0 and start >= end) or (step < 0 and start <= end):
                    logger.warning("Nenhuma rolagem ocorrerá devido a valores de start/end incorretos.")
                    return

                position = start
                previous_position = None  # Rastrear a posição anterior para evitar rolagens duplicadas
                while (step > 0 and position < end) or (step < 0 and position > end):
                    if position == previous_position:
                        logger.debug(f"Parando rolagem pois a posição não mudou: {position}")
                        break

                    try:
                        self.driver.execute_script(script_scroll_to, element, position)
                        logger.debug(f"Rolado para a posição: {position}")
                    except Exception as e:
                        logger.error(f"Erro durante a rolagem: {e}")

                    previous_position = position
                    position += step

                    # Diminuir o passo, mas garantir que não inverta a direção
                    step = max(10, abs(step) - 10) * (-1 if reverse else 1)

                    time.sleep(random.uniform(0.6, 1.5))

                # Garantir que a posição final de rolagem esteja correta
                self.driver.execute_script(script_scroll_to, element, end)
                logger.debug(f"Rolado para a posição final: {end}")
                time.sleep(0.5)
            else:
                logger.warning("O elemento não está visível.")
        except Exception as e:
            logger.error(f"Exceção ocorrida durante a rolagem: {e}")

    def clear_cookies(self, site_url, quit=True):
        logger.debug(f"Limpando cookies para o site: {site_url}")
        driver = self.header_configuration(headless=True)
        driver.get(site_url)
        driver.delete_all_cookies()
        logger.debug("Cookies deletados com sucesso!")
        if quit:
            driver.quit()

    def get_current_index(self, control):
        control_file = f"{control}.txt"
        if os.path.exists(control_file):
            with open(control_file, "r") as file:
                return int(file.read().strip())
        return 0

    def update_current_index(self, index, control):
        control_file = f"{control}.txt"
        with open(control_file, "w") as file:
            file.write(str(index))
    
    def find_chrome_processes(self):
        chrome_processes = []
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == 'chrome.exe':
                chrome_processes.append(proc)
        return chrome_processes

    def kill_chrome_processes(self):
        chrome_processes = self.find_chrome_processes()
        for process in chrome_processes:
            try:
                subprocess.run(['taskkill', '/F', '/PID', str(process.pid)], check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Falha ao encerrar o processo {process.pid}: {e}")
    
    # def scrape_with_captcha_retry(self, url_atual, url_objetivo):
    #     i = 0
    #     while "validate.perfdrive.com" in url_atual:
    #         time.sleep(random.randint(4,7))
    #         i += 1
    #         logger.warning(f"Captcha detectado. Tentando novamente... Tentativa {i}")
    #         self.kill_chrome_processes()

    #         try:
    #             self.driver.service.process.terminate()
    #             self.driver.quit()
    #         except Exception as e:
    #             logger.error(f"Erro ao fechar o driver: {e}")
            
    #         self.delete_cache(get_previous_url=False)
    #         time.sleep(12)
    #         self.driver = self.header_configuration(headless=True)

    #         if i > 1:
    #             vpn_changer.change_ip()
    #             self.driver.get(url_objetivo)
    #             logger.debug(f"URL atual: {self.driver.current_url}")
    #             self.driver.delete_all_cookies()
    #         else:
    #             self.driver.get(url_objetivo)
    #             logger.debug(f"URL atual: {self.driver.current_url}")

    #         self.driver.get(url_objetivo)
    #         logger.debug(f"URL atual: {self.driver.current_url}")
    #         url_atual = self.driver.current_url
    #     logger.info('Captcha contornado com sucesso')
    #     return self.driver
