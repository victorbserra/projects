import pandas as pd
import requests
import json
import time
import random
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def carregar_tabela_referencia():
    url = 'https://veiculos.fipe.org.br/api/veiculos/ConsultarTabelaDeReferencia'

    try:
        response = requests.post(url, timeout=6, verify=False)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f'Ocorreu um erro HTTP: {http_err}')
    except requests.exceptions.ConnectionError as conn_err:
        print(f'Erro ao conectar: {conn_err}')
    except requests.exceptions.Timeout as timeout_err:
        print(f'Erro de tempo limite: {timeout_err}')
    except requests.exceptions.RequestException as req_err:
        print(f'Erro: {req_err}')

def consultar_marcas(tbl_ref, tbl_veiculo):
    url = 'https://veiculos.fipe.org.br/api/veiculos/ConsultarMarcas'
    headers = {'Content-Type': 'application/json'}
    data = {
        'codigoTabelaReferencia': tbl_ref,
        'codigoTipoVeiculo': tbl_veiculo,
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f'Ocorreu um erro HTTP: {http_err}')
    except requests.exceptions.ConnectionError as conn_err:
        print(f'Erro ao conectar: {conn_err}')
    except requests.exceptions.Timeout as timeout_err:
        print(f'Erro de tempo limite: {timeout_err}')
    except requests.exceptions.RequestException as req_err:
        print(f'Erro: {req_err}')

def consultar_modelos(cod_marca, tbl_ref):
    url = 'https://veiculos.fipe.org.br/api/veiculos/ConsultarModelos'
    headers = {'Content-Type': 'application/json'}
    data = {
        'codigoTabelaReferencia': tbl_ref,
        'codigoTipoVeiculo': '1',
        'codigoMarca': cod_marca,
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as http_err:
        print(f'Ocorreu um erro HTTP: {http_err}')
    except requests.exceptions.ConnectionError as conn_err:
        print(f'Erro ao conectar: {conn_err}')
    except requests.exceptions.Timeout as timeout_err:
        print(f'Erro de tempo limite: {timeout_err}')
    except requests.exceptions.RequestException as req_err:
        print(f'Erro: {req_err}')

tb_ref_data = carregar_tabela_referencia()
tb_ref_data = pd.DataFrame(tb_ref_data)

codVeiculo = {
    'cod_tipo_veiculo': [1, 2, 3],
    'veiculo': ['carro', 'moto', 'caminhao']
}

codVeiculo = pd.DataFrame(codVeiculo)

marcas_veiculos = []
for i in range(len(codVeiculo)):
    time.sleep(random.randint(1, 3))
    marcas = consultar_marcas(str(tb_ref_data['Codigo'].max()), str(i + 1))
    marcas = [{'Value': marca['Value'], 'Label': marca['Label'], 'cod_veiculo': i + 1} for marca in marcas]
    marcas_veiculos.extend(marcas)

modelos_veiculos = []
for marca in marcas_veiculos:
    time.sleep(random.randint(1, 3))
    modelos = consultar_modelos(marca['Value'], str(tb_ref_data['Codigo'].max()))
    if 'Modelos' in modelos:
        modelos = [{'Value': modelo['Value'], 'Label': modelo['Label'], 'cod_veiculo': marca['cod_veiculo']} for modelo in modelos['Modelos']]
        modelos_veiculos.extend(modelos)

df_modelos = pd.DataFrame(modelos_veiculos)
df_modelos.head()
