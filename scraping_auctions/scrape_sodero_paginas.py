import pandas as pd
import time as time
import random
import os
from google.cloud import bigquery
from google.oauth2 import service_account
from urllib.parse import urlparse, urljoin
from datetime import datetime
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from azure.storage.blob import BlobServiceClient
from config import new_chromedriver_path, user_agents, path
from web_scraper import WebScraper
from vpn import VPNChanger

lista_sites = pd.read_csv('lista_sites.csv', sep=';')
lista_sites = lista_sites['0'].tolist()

df_sodero = pd.read_csv('df_sodero.csv', sep=';')
df_lista = df_sodero['Leilao'].apply(lambda x: urljoin(lista_sites[0], x))

scraper = WebScraper(new_chromedriver_path, user_agents, path)
vpn_changer = VPNChanger()
vpn_files = vpn_changer.get_vpn_files()
key_path = "leiloes-391501-477564df1a41.json"
credentials = service_account.Credentials.from_service_account_file(key_path)
client = bigquery.Client(credentials=credentials, project=credentials.project_id)

#if os.path.exists('bens.csv'):
#    os.remove('bens.csv')
#if os.path.exists('infos_especificas.csv'):
#    os.remove('infos_especificas.csv')
#if os.path.exists('df_intermediario.csv'):
#    os.remove('df_intermediario.csv')
#if os.path.exists('df_leilao_aberto.csv'):
#    os.remove('df_leilao_aberto.csv')
#if os.path.exists('df_leilao_encerrado.csv'):
#    os.remove('df_leilao_encerrado.csv')
#if os.path.exists('df_concat.csv'):
#    os.remove('df_concat.csv')
#if os.path.exists('control_home.txt'):
#    os.remove('control_home.txt')
#if  os.path.exists('control_pag.txt'):
#    os.remove('control_pag.txt')

def scrape_aberto(lista_bens):
    df_intermediario = pd.DataFrame()
    infos_base = []
    for inf in lista_bens:
        titulo = inf.find('h2', class_='titulo')
        titulo = titulo.text if titulo else None

        link = inf.find('a', class_='link')
        link = link.get('href') if link else None

        imagem = inf.find('img', class_='imagemDisponivel img-responsive')
        imagem = imagem.get('src') if imagem else None

        status_lote = inf.find('div', class_='statusLote statusLote-Aguardando')
        status_lote = status_lote.text if status_lote else None

        lance_atual = inf.find('span', class_='lance-atual')
        lance_atual = lance_atual.get('title') if lance_atual else None

        visitas_lances = inf.find('span', class_='visitas-lances')
        visitas_lances = visitas_lances.text if visitas_lances else None

        infos_base.append(
            {
                'Titulo': titulo,
                'Imagem': imagem,
                'Link': link,
                'Status Lote': status_lote,
                'Lance Atual': lance_atual,
                
                'Visitas_lances': visitas_lances
            }
        )
        
        df_bens = pd.DataFrame(infos_base).replace(r'\n|\t', '', regex=True)
        df_bens.to_csv('bens.csv', sep = ';', index=False)
    if os.path.exists('df_intermediario.csv'):
        df_intermediario = pd.read_csv('df_intermediario.csv', sep = ';')
    df_intermediario = pd.concat([df_intermediario, df_bens], axis=0)
    df_intermediario.to_csv('df_intermediario.csv', sep = ';', index=False)

    return df_intermediario

###################################################################################################
# Envio para o BigQuery
def enviar_bigquery():
    df_leilao_aberto = pd.read_csv('df_leilao_aberto.csv', sep=';')
    df_leilao_aberto = df_leilao_aberto.drop_duplicates()
    df_leilao_aberto = df_leilao_aberto.drop(columns=['Link'])
    df_leilao_aberto = df_leilao_aberto.rename(columns={
        'Titulo': 'titulo',
        'Imagem': 'imagem',
        'Status Lote':'status_lote',
        'Lance Atual': 'lance_atual',
        'Visitas_lances': 'visitas_lances',
        'link_clicavel': 'link',
        'data_hora_atualizacao': 'data_hora_atualizacao'
    })

    project_id = 'leiloes-391501'
    dataset_name = 'origem_scrape_leiloes'
    table_name = 'raw-leilao-aberto'

    schema = [
        bigquery.SchemaField("titulo", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("imagem", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("status_lote", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("lance_atual", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("visitas_lances", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("link", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("data_hora_atualizacao", "STRING", mode="NULLABLE"),
    ]

    table_ref = client.dataset(dataset_name).table(table_name)
    try:
        client.get_table(table_ref)
        print('A tabela já existe. Os novos dados serão adicionados a ela.')
    except:
        print('A tabela não existe. Uma nova tabela será criada.')
        table = bigquery.Table(table_ref, schema=schema)
        table = client.create_table(table)
        print('Tabela criada com sucesso.')

    job_config = bigquery.LoadJobConfig(schema=schema)
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

    load_job = client.load_table_from_dataframe(df_leilao_aberto, table_ref, job_config=job_config)
    print("Starting job {}".format(load_job.job_id))

    load_job.result()
    print("Job finished.")

    destination_table = client.get_table(table_ref)
    print("Loaded {} rows.".format(destination_table.num_rows))

    clean_leilao_aberto = df_leilao_aberto.copy()
    clean_leilao_aberto[['leilao', 'temp']] = clean_leilao_aberto['titulo'].str.split(' - ', n=1, expand=True)
    clean_leilao_aberto[['lote', 'bem']] = clean_leilao_aberto['temp'].str.split(' - ', n=1, expand=True)
    clean_leilao_aberto = clean_leilao_aberto.drop(columns=['titulo','temp'])
    clean_leilao_aberto['id_leilao'] = clean_leilao_aberto['leilao'].str.extract('(\d+)$')
    clean_leilao_aberto['visitas_lances'] = clean_leilao_aberto['visitas_lances'].str.replace('Visitas: ', '').str.replace(' | Lances: ', ',')
    clean_leilao_aberto[['visitas', 'lances']] = clean_leilao_aberto['visitas_lances'].str.split(',', expand=True)
    clean_leilao_aberto = clean_leilao_aberto.drop(columns=['visitas_lances'])

    project_id = 'leiloes-391501'
    dataset_name = 'origem_scrape_leiloes'
    table_name = 'clean-leilao-aberto'

    schema = [
        bigquery.SchemaField("leilao", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("lote", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("bem", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("id_leilao", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("imagem", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("status_lote", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("lance_atual", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("link", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("visitas", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("lances", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("data_hora_atualizacao", "STRING", mode="NULLABLE"),
    ]

    table_ref = client.dataset(dataset_name).table(table_name)
    try:
        client.get_table(table_ref)
        print('A tabela já existe. Os novos dados serão adicionados a ela.')
    except:
        print('A tabela não existe. Uma nova tabela será criada.')
        table = bigquery.Table(table_ref, schema=schema)
        table = client.create_table(table)
        print('Tabela criada com sucesso.')

    job_config = bigquery.LoadJobConfig(schema=schema)
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

    load_job = client.load_table_from_dataframe(clean_leilao_aberto, table_ref, job_config=job_config)
    print("Starting job {}".format(load_job.job_id))

    load_job.result()
    print("Job finished.")

    destination_table = client.get_table(table_ref)
    print("Loaded {} rows.".format(destination_table.num_rows))


start_index = scraper.get_current_index("control_home")
vpn_changer.connect_vpn(vpn_files[random.randint(0, len(vpn_files) - 1)])

df_leilao_aberto = pd.DataFrame()
try:
    for x in range(start_index, len(df_lista)):
        scraper.driver = scraper.header_configuration(headless=True)   
        time.sleep(random.randint(13,16))
        f = df_lista.iloc[x]
        
        if x % 5 == 0 and x > 0:
           vpn_changer.change_ip()

        if x % 20 == 0 and x > 0:
            scraper.driver.get(lista_sites[0])

        scraper.driver.get(f'{f}ordenacao/nu_lote/tipo-ordenacao/crescente/qtde-itens/{random.randint(4000,6000)}/')
        scraper.driver.delete_all_cookies()

        print(scraper.driver.current_url)
        if "validate.perfdrive.com" in urlparse(scraper.driver.current_url).netloc:
            scraper.driver = scraper.scrape_with_captcha_retry(scraper.driver.current_url, f'{f}ordenacao/nu_lote/tipo-ordenacao/crescente/qtde-itens/{random.randint(4000,6000)}/') #, df_lista
        if 'encerrado' in scraper.driver.current_url:
            continue

        soup = BeautifulSoup(scraper.driver.page_source, 'html.parser')
        
        try:
            span = soup.find('span', class_='textoAux2')
            if span.text == 'Leilão não encontrado!':
                continue
        except:
            pass

        ul_paginas = soup.find('ul', class_='tipo-vizualizacao visual_imagemlista')
        lista_bens = ul_paginas.find_all('li', attrs={'guardar': True})

        df_aberto = scrape_aberto(lista_bens)
        if os.path.exists('df_leilao_aberto.csv'):
            df_leilao_aberto = pd.read_csv('df_leilao_aberto.csv', sep = ';')
        df_leilao_aberto = pd.concat([df_leilao_aberto, df_aberto], axis=0)
        df_leilao_aberto = df_leilao_aberto.drop_duplicates()
        df_leilao_aberto['link_clicavel'] = df_leilao_aberto['Link'].apply(lambda x: urljoin(lista_sites[0], x))
        df_leilao_aberto['data_hora_atualizacao'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        df_leilao_aberto.to_csv('df_leilao_aberto.csv', sep = ';', index=False)

        print(f"Index {x + 1} of {len(df_lista)}")
        scraper.update_current_index(x + 1, "control_home")
        scraper.driver.quit()
        
        scraper.kill_chrome_processes()
        scraper.delete_cache(get_previous_url=False)
    
    vpn_changer.disconnect_vpn()
    print(f'Finalizado as {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}')
finally:
    try:
        vpn_changer.disconnect_vpn()
        scraper.driver.service.process.terminate()
        scraper.driver.quit()
        scraper.delete_cache(get_previous_url=False)
    except:
        pass

# enviar para o blob do azure
enviar_bigquery()
