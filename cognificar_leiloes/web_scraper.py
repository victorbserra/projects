import pandas as pd
import numpy as np
import time as time
import random
import os
import shutil
import psutil
import subprocess
from urllib.parse import urlparse, urljoin
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.common.proxy import Proxy, ProxyType
from config import proxy_ip_port, proxy_user_pass
from vpn import VPNChanger

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

    def header_configuration(self, headless=True):
        webdriver_service = Service(self.chromedriver_path)

        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        # chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument(f'--user-agent={random.choice(self.user_agents)}')
        chrome_options.add_argument(f'--user-data-dir={self.cache_path}')

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
        if url_atual:
            try:
                url_atual = self.driver.current_url if get_previous_url else None
            except Exception as e:
                print(f"O driver já foi fechado. Erro: {e}")
        try:
            self.driver.quit()
        except Exception as e:
            print(f"Não foi possível fechar o driver. Erro: {e}")
        if os.path.exists(self.cache_path):
            shutil.rmtree(self.cache_path)
            print("Cache deletado com sucesso!")
        if url_atual:
            self.driver.get(url_atual)

    def scroll(self, min, max):
        scroll_amount = random.uniform(min, max)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
        time.sleep(random.uniform(1, 2))
    
    def clear_cookies(self, site_url,quit=True):
        driver = self.header_configuration(headless=True)
        driver.get(site_url)
        driver.delete_all_cookies()
        print(driver.current_url)
        print("Cookies deletados com sucesso!")
        if quit:
            self.driver.quit()

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
               pass

    def scrape_with_captcha_retry(self, url_atual, url_objetivo):
        i = 0
        while "validate.perfdrive.com" in url_atual:
            time.sleep(random.randint(4,7))
            i += 1
            print(f"Captcha detected. Retrying... Tentativa {i}")
            self.kill_chrome_processes()

            try:
                self.driver.service.process.terminate()
                self.driver.quit()
            except:
                pass
            
            self.delete_cache(get_previous_url=False)
            time.sleep(12)
            self.driver = self.header_configuration(headless=True)

            if i > 1:
               vpn_changer.change_ip()
               self.driver.get(url_objetivo)
               print(self.driver.current_url)
               self.driver.delete_all_cookies()
            else:
               self.driver.get(url_objetivo)
               print(self.driver.current_url)

            self.driver.get(url_objetivo)
            print(self.driver.current_url)
            url_atual = self.driver.current_url
        print('captcha quebrado')
        return self.driver