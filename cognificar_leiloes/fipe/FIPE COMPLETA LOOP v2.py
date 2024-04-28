import os
import csv
import asyncio
import aiohttp

projeto_fipe_path = os.path.expanduser("~/Documents/Projeto FIPE")
progress_file_path = os.path.join(projeto_fipe_path, "progresso_fipe.txt")

def formatar_valor(valor):
    return valor.replace("R$", "").replace(".", "").replace(",", ".").strip()

def save_to_csv(results):
    csv_path = os.path.join(projeto_fipe_path, "resultados_fipe.csv")
    file_exists = os.path.exists(csv_path)

    with open(csv_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["Marca", "Modelo", "Ano", "Valor", "Combustível", "Código Fipe", "Mês Referência", "Autenticação", "Tipo Veículo", "Sigla Combustível", "Data Consulta"])
        for result in results:
            writer.writerow(result)

def log_result(params, output):
    # Utilizamos o encoding 'utf-8' para evitar problemas com caracteres especiais
    print("Params:", params)
    print("Output:", output)
    print("=" * 50)

def save_progress(marca_index, modelo_index, ano_index, referencia_index):
    with open(progress_file_path, mode="w", encoding="utf-8") as file:
        file.write(f"{marca_index}\n")
        file.write(f"{modelo_index}\n")
        file.write(f"{ano_index}\n")
        file.write(f"{referencia_index}\n")

def load_progress():
    if not os.path.exists(progress_file_path):
        return None

    with open(progress_file_path, mode="r", encoding="utf-8") as file:
        marca_index = int(file.readline().strip())
        modelo_index = int(file.readline().strip())
        ano_index = int(file.readline().strip())
        referencia_index = int(file.readline().strip())

    return marca_index, modelo_index, ano_index, referencia_index

async def fetch(session, url, body):
    async with session.post(url, json=body) as response:
        if response.status == 200:
            return await response.json()
        else:
            raise Exception(f"Erro na requisição. Código de status: {response.status}")

async def get_referencia_mensal():
    url = "http://veiculos.fipe.org.br/api/veiculos/ConsultarTabelaDeReferencia"
    headers = {
        "Host": "veiculos.fipe.org.br",
        "Referer": "http://veiculos.fipe.org.br",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        response = await fetch(session, url, {})
        return [item["Codigo"] for item in response]

async def get_codigo_marca(codigo_referencia):
    url = "http://veiculos.fipe.org.br/api/veiculos/ConsultarMarcas"
    headers = {
        "Host": "veiculos.fipe.org.br",
        "Referer": "http://veiculos.fipe.org.br",
        "Content-Type": "application/json"
    }
    body = {
        "codigoTabelaReferencia": codigo_referencia,
        "codigoTipoVeiculo": 1
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        response = await fetch(session, url, body)
        return response

async def get_codigo_modelo(codigo_referencia, codigo_marca):
    url = "http://veiculos.fipe.org.br/api/veiculos/ConsultarModelos"
    headers = {
        "Host": "veiculos.fipe.org.br",
        "Referer": "http://veiculos.fipe.org.br",
        "Content-Type": "application/json"
    }
    body = {
        "codigoTabelaReferencia": codigo_referencia,
        "codigoTipoVeiculo": 1,
        "codigoMarca": codigo_marca
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        response = await fetch(session, url, body)
        return response["Modelos"]

async def get_codigo_ano(codigo_referencia, codigo_marca, codigo_modelo):
    url = "http://veiculos.fipe.org.br/api/veiculos/ConsultarAnoModelo"
    headers = {
        "Host": "veiculos.fipe.org.br",
        "Referer": "http://veiculos.fipe.org.br",
        "Content-Type": "application/json"
    }
    body = {
        "codigoTabelaReferencia": codigo_referencia,
        "codigoTipoVeiculo": 1,
        "codigoMarca": codigo_marca,
        "codigoModelo": codigo_modelo
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        response = await fetch(session, url, body)
        return response

async def get_valor_veiculo(codigo_referencia, codigo_marca, codigo_modelo, codigo_ano):
    url = "http://veiculos.fipe.org.br/api/veiculos/ConsultarValorComTodosParametros"
    headers = {
        "Host": "veiculos.fipe.org.br",
        "Referer": "http://veiculos.fipe.org.br",
        "Content-Type": "application/json"
    }
    body = {
        "codigoTabelaReferencia": codigo_referencia,
        "codigoTipoVeiculo": 1,
        "codigoMarca": codigo_marca,
        "codigoModelo": codigo_modelo,
        "ano": codigo_ano,
        "codigoTipoCombustivel": 1,
        "anoModelo": int(codigo_ano.split('-')[0]),
        "tipoConsulta": "tradicional"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
        response = await fetch(session, url, body)
        return response

async def get_all_vehicle_prices_async():
    if not os.path.exists(projeto_fipe_path):
        os.makedirs(projeto_fipe_path)

    csv_path = os.path.join(projeto_fipe_path, "resultados_fipe.csv")
    first_run = not os.path.exists(csv_path)

    progress = load_progress()

    referencias = await get_referencia_mensal()

    referencia_index = progress[3] if progress else 0

    async with aiohttp.ClientSession(headers={
        "Host": "veiculos.fipe.org.br",
        "Referer": "http://veiculos.fipe.org.br",
        "Content-Type": "application/json"
    }) as session:

        for codigo_referencia in referencias[referencia_index:]:

            marcas = await get_codigo_marca(codigo_referencia)

            marca_index = progress[0] if progress and progress[3] == referencia_index else 0

            for marca in marcas[marca_index:]:

                codigo_marca = marca["Value"]
                modelos = await get_codigo_modelo(codigo_referencia, codigo_marca)

                modelo_index = progress[1] if progress and progress[3] == referencia_index and progress[0] == marca_index else 0

                for modelo in modelos[modelo_index:]:
                    codigo_modelo = modelo["Value"]
                    anos = await get_codigo_ano(codigo_referencia, codigo_marca, codigo_modelo)

                    ano_index = progress[2] if progress and progress[3] == referencia_index and progress[0] == marca_index and progress[1] == modelo_index else 0

                    results_to_save = []

                    for ano in anos[ano_index:]:
                        codigo_ano = ano["Value"]
                        resultado_final = await get_valor_veiculo(codigo_referencia, codigo_marca, codigo_modelo, codigo_ano)
                        log_result({"codigoTabelaReferencia": codigo_referencia, "codigoTipoVeiculo": 1, "codigoMarca": codigo_marca, "codigoModelo": codigo_modelo, "ano": codigo_ano}, resultado_final)

                        if not ("codigo" in resultado_final and resultado_final["codigo"] == "0" and "erro" in resultado_final and resultado_final["erro"] == "nadaencontrado"):
                            valor_formatado = formatar_valor(resultado_final["Valor"])
                            results_to_save.append([resultado_final["Marca"], resultado_final["Modelo"], resultado_final["AnoModelo"], valor_formatado,
                                                   resultado_final["Combustivel"], resultado_final["CodigoFipe"], resultado_final["MesReferencia"],
                                                   resultado_final["Autenticacao"], resultado_final["TipoVeiculo"], resultado_final["SiglaCombustivel"],
                                                   resultado_final["DataConsulta"]])

                        ano_index += 1
                        save_progress(marca_index, modelo_index, ano_index, referencia_index)

                        if results_to_save:
                            save_to_csv(results_to_save)
                            results_to_save.clear()

                    modelo_index += 1
                    save_progress(marca_index, modelo_index, ano_index, referencia_index)

                marca_index += 1
                save_progress(marca_index, modelo_index, ano_index, referencia_index)

            referencia_index += 1
            save_progress(marca_index, modelo_index, ano_index, referencia_index)

    if results_to_save:
        save_to_csv(results_to_save)

if __name__ == "__main__":
    asyncio.run(get_all_vehicle_prices_async())
