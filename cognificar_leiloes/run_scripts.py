import subprocess
import logging

# Criar um logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Criar um manipulador de log que escreve para um arquivo
handler = logging.FileHandler('script_log.log')
handler.setLevel(logging.INFO)

# Criar um manipulador de log que escreve no console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Criar um formatador de log
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Adicione o formatador ao manipulador
handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Adicione o manipulador ao logger
logger.addHandler(handler)
logger.addHandler(console_handler)

logger.info('Iniciando o script')
script_state_file = 'script_state.json'

scripts = [
    'scrape_sodero_home.py',
    'scrape_sodero_paginas.py',
]

max_retries = 5

for script in scripts:
    for attempt in range(max_retries):
        try:
            subprocess.check_call(['python', script])  # Note a mudança para check_call
            break  # Se o script foi executado com sucesso, saia do loop
        except subprocess.CalledProcessError:
            logger.exception(f"Erro ao executar o script {script}, tentativa {attempt + 1} de {max_retries}")
            if attempt + 1 == max_retries:
                logger.error(f"O script {script} falhou após {max_retries} tentativas")