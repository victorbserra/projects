import pandas as pd
import time as time
import random
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime
from bs4 import BeautifulSoup
from web_scraper import WebScraper
from vpn import VPNChanger
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, urljoin
from azure.storage.blob import BlobServiceClient
from config import user_agents, path, new_chromedriver_path, connection_string

scraper = WebScraper(new_chromedriver_path, user_agents, path)
vpn_changer = VPNChanger()
vpn_files = vpn_changer.get_vpn_files()

lista_sites = pd.read_csv('lista_sites.csv', sep=';')
lista_sites = lista_sites['0'].tolist()
key_path = "leiloes-391501-477564df1a41.json"
credentials = service_account.Credentials.from_service_account_file(key_path)

###################################################################################################
# Envio para o BigQuery
def enviar_bigquery():
    envio_sodero = pd.read_csv('df_sodero.csv', sep=';')
    envio_sodero = envio_sodero.rename(columns={
        'Titulo': 'titulo',
        'Leilao':'leilao',
        'Segmento': 'segmento',
        'Tipo Categoria': 'tipo_categoria',
        'situacao': 'situacao',
        'data_hora': 'data_hora_atualizacao'
    })  

    print(envio_sodero)
    client = bigquery.Client(credentials=credentials, project=credentials.project_id)
    project_id = 'leiloes-391501'
    dataset_name = 'origem_scrape_leiloes'
    table_name = 'raw-df-sodero'

    schema_raw = [
        bigquery.SchemaField("titulo", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("leilao", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("segmento", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("tipo_categoria", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("situacao", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("data_hora_atualizacao", "STRING", mode="NULLABLE")
    ]
    table_ref = client.dataset(dataset_name).table(table_name)
    try:
        client.get_table(table_ref)
        print('A tabela já existe. Os novos dados serão adicionados a ela.')
    except:
        print('A tabela não existe. Uma nova tabela será criada.')
        table = bigquery.Table(table_ref, schema=schema_raw)
        table = client.create_table(table)
        print('Tabela criada com sucesso.')


    job_config = bigquery.LoadJobConfig(schema=schema_raw)
    job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

    load_job = client.load_table_from_dataframe(envio_sodero, table_ref, job_config=job_config)
    print("Starting job {}".format(load_job.job_id))

    load_job.result()
    print("Job finished.")

    destination_table = client.get_table(table_ref)
    print("Loaded {} rows.".format(destination_table.num_rows))

    clean_df_sodero = envio_sodero.copy()

    clean_df_sodero['id_leilao'] = clean_df_sodero['leilao'].str.extract(r'(\d+)')
    clean_df_sodero['segmento'] = clean_df_sodero['segmento'].str.lower()
    clean_df_sodero[['segmento', 'qtd_bens']] = clean_df_sodero['segmento'].str.extract(r'(.+)\s\((\d+)\)', expand=True)
    clean_df_sodero['segmento'] = clean_df_sodero['segmento'].str.strip()
    clean_df_sodero = clean_df_sodero.drop(columns=['leilao'])

    project_id = 'leiloes-391501'
    dataset_name = 'origem_scrape_leiloes'
    table_name = 'clean-df-sodero'

    schema = [
        bigquery.SchemaField("titulo", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("segmento", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("qtd_bens", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("tipo_categoria", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("situacao", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("data_hora_atualizacao", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("id_leilao", "STRING", mode="NULLABLE")
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

    load_job = client.load_table_from_dataframe(clean_df_sodero, table_ref, job_config=job_config)
    print("Starting job {}".format(load_job.job_id))

    load_job.result()
    print("Job finished.")

    destination_table = client.get_table(table_ref)
    print("Loaded {} rows.".format(destination_table.num_rows))

vpn_changer.connect_vpn(vpn_files[random.randint(0, len(vpn_files) - 1)])
driver = scraper.header_configuration(headless=True)
driver.delete_all_cookies()
driver.get(lista_sites[0])
print(driver.current_url)
try:
  soup = BeautifulSoup(driver.page_source, 'html.parser')
  div = soup.find('div', id='atualizacaoHome')
  ul = div.find('ul', class_='act-agenda-alterado ag_destaques_leilao-leiloes padrao ativos')
  li = ul.find_all('li', class_='leilao_visualizacao-4')

  information = []
  for i in li:
      titulo = i.find('span', class_='leilao_visualizacao-4-tit')
      titulo = titulo.text if titulo else None

      link = i.find('a', class_='descricao')
      link = link.get('href') if link else None

      segmento = i.find('p', class_='segmento')
      segmento = segmento.text if segmento else None

      tipo_categoria = i.find('p', class_='agenda_tipo_categoria') 
      tipo_categoria = tipo_categoria.text if tipo_categoria else None

      situacao = i.find('div', class_='info-adicional') or i.find('div', class_='info-adicionoal')
      
      information.append(
          { 'Titulo': titulo,
            'Leilao': link,
            'Segmento': segmento,
            'Tipo Categoria': tipo_categoria,
            'situacao': situacao.text
          }
      )
  df_sodero = pd.DataFrame(information)
  df_sodero = df_sodero.replace(r'\n|\t', '', regex=True)
  df_sodero['data_hora'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
  df_lista = df_sodero['Leilao'].apply(lambda x: urljoin(lista_sites[0], x))
  df_sodero.to_csv('df_sodero.csv', sep = ';', index=False)
finally:
  print('Raspagem na home page finalizada.')
  driver.quit()
  vpn_changer.disconnect_vpn()

# enviar para o blob do azure
enviar_bigquery()