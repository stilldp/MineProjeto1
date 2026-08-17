import csv
import re
from datetime import datetime
from pathlib import Path


# ============================================================
# CONFIGURAÇÕES DO PROJETO
# ============================================================

ARQUIVO_PRODUTOS = Path("olist_products_dataset.csv")
ARQUIVO_PEDIDOS = Path("olist_orders_dataset.csv")
PASTA_SAIDA = Path("saida")

COLUNAS_DIMENSOES = [
    "product_weight_g",
    "product_length_cm",
    "product_height_cm",
    "product_width_cm",
]

# Função anônima usada para centralizar a regra de valor ausente.
valor_ausente = lambda valor: valor is None or str(valor).strip() == ""


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def limpar_categoria(categoria):
    """
    Padroniza o nome da categoria:
    1. Trata valor vazio como 'sem categoria';
    2. Remove espaços do início/fim com strip();
    3. Converte para minúsculas com lower();
    4. Remove caracteres especiais/pontuações com Regex;
    5. Remove espaços repetidos.
    """
    if valor_ausente(categoria):
        return "sem categoria"

    categoria = categoria.strip().lower()

    # Mantém letras, números, espaços e underline.
    # A faixa À-ÿ permite preservar caracteres acentuados.
    categoria = re.sub(r"[^a-z0-9_À-ÿ\s]", "", categoria)

    # Substitui sequências de espaços por apenas um espaço.
    categoria = re.sub(r"\s+", " ", categoria).strip()

    # Caso a categoria tivesse somente caracteres inválidos.
    if categoria == "":
        return "sem categoria"

    return categoria


def converter_numero(valor):
    """
    Tenta converter um texto em float.
    Retorna None quando o campo estiver vazio ou não for numérico.
    """
    if valor_ausente(valor):
        return None

    try:
        return float(str(valor).strip().replace(",", "."))
    except ValueError:
        return None


def calcular_medias_dimensoes(caminho_csv):
    """
    Faz uma primeira leitura do CSV de produtos para calcular manualmente
    a média de cada dimensão física.

    Escolha técnica:
    Em vez de excluir produtos com dimensão ausente, usamos a média dos
    valores válidos. Isso preserva os registros e evita perda de informação.
    A média é uma imputação simples e adequada para este exercício de ETL,
    embora em um projeto real de ML devam ser avaliados outliers e a
    distribuição de cada variável antes de escolher a estratégia.
    """
    somas = {coluna: 0.0 for coluna in COLUNAS_DIMENSOES}
    quantidades = {coluna: 0 for coluna in COLUNAS_DIMENSOES}

    with open(caminho_csv, "r", encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)

        for linha in leitor:
            for coluna in COLUNAS_DIMENSOES:
                numero = converter_numero(linha.get(coluna))

                if numero is not None and numero > 0:
                    somas[coluna] += numero
                    quantidades[coluna] += 1

    medias = {}

    for coluna in COLUNAS_DIMENSOES:
        if quantidades[coluna] > 0:
            medias[coluna] = somas[coluna] / quantidades[coluna]
        else:
            # Proteção para o caso extremo de uma coluna inteira estar vazia.
            medias[coluna] = 0.0

    return medias


def sanitizar_produtos(caminho_entrada, caminho_saida):
    """
    Sanitiza a tabela de produtos e grava um novo CSV.
    Retorna um dicionário com estatísticas do processamento.
    """
    medias = calcular_medias_dimensoes(caminho_entrada)

    estatisticas = {
        "total_produtos": 0,
        "categorias_corrigidas": 0,
        "dimensoes_corrigidas": 0,
        "total_nulos_corrigidos": 0,
    }

    with open(caminho_entrada, "r", encoding="utf-8-sig", newline="") as entrada:
        leitor = csv.DictReader(entrada)

        if leitor.fieldnames is None:
            raise ValueError("O arquivo de produtos não possui cabeçalho.")

        with open(caminho_saida, "w", encoding="utf-8", newline="") as saida:
            escritor = csv.DictWriter(saida, fieldnames=leitor.fieldnames)
            escritor.writeheader()

            for linha in leitor:
                estatisticas["total_produtos"] += 1

                categoria_original = linha.get("product_category_name", "")

                if valor_ausente(categoria_original):
                    estatisticas["categorias_corrigidas"] += 1
                    estatisticas["total_nulos_corrigidos"] += 1

                linha["product_category_name"] = limpar_categoria(
                    categoria_original
                )

                for coluna in COLUNAS_DIMENSOES:
                    numero = converter_numero(linha.get(coluna))

                    if numero is None:
                        linha[coluna] = f"{medias[coluna]:.2f}"
                        estatisticas["dimensoes_corrigidas"] += 1
                        estatisticas["total_nulos_corrigidos"] += 1
                    elif numero <= 0:
                        # Valores físicos iguais ou menores que zero também
                        # são considerados inconsistentes e recebem a média.
                        linha[coluna] = f"{medias[coluna]:.2f}"
                        estatisticas["dimensoes_corrigidas"] += 1
                    else:
                        # Mantém o valor original válido.
                        linha[coluna] = str(linha[coluna]).strip()

                escritor.writerow(linha)

    estatisticas["medias_dimensoes"] = medias
    return estatisticas


def formatar_data_brasileira(data_texto):
    """
    Converte 'AAAA-MM-DD HH:MM:SS' para 'DD/MM/AAAA'.

    Se a data estiver vazia, retorna string vazia.
    Se houver um formato inesperado, retorna o valor original para evitar
    perda silenciosa de informação.
    """
    if valor_ausente(data_texto):
        return ""

    data_texto = data_texto.strip()

    try:
        data = datetime.strptime(data_texto, "%Y-%m-%d %H:%M:%S")
        return data.strftime("%d/%m/%Y")
    except ValueError:
        return data_texto


def processar_pedidos(
    caminho_entrada,
    caminho_saida,
    caminho_entrega_nula,
    caminho_entrega_nula_nao_cancelada,
):
    """
    Processa pedidos, formata order_approved_at e valida a hipótese:

    'Toda order_delivered_customer_date vazia ocorre porque
    order_status == canceled?'

    Também separa os pedidos com entrega nula em arquivos próprios.
    """
    estatisticas = {
        "total_pedidos": 0,
        "pedidos_cancelados": 0,
        "entregas_nulas": 0,
        "entregas_nulas_canceladas": 0,
        "entregas_nulas_nao_canceladas": 0,
        "datas_aprovacao_formatadas": 0,
    }

    with open(caminho_entrada, "r", encoding="utf-8-sig", newline="") as entrada:
        leitor = csv.DictReader(entrada)

        if leitor.fieldnames is None:
            raise ValueError("O arquivo de pedidos não possui cabeçalho.")

        fieldnames = leitor.fieldnames

        with (
            open(caminho_saida, "w", encoding="utf-8", newline="") as saida,
            open(caminho_entrega_nula, "w", encoding="utf-8", newline="") as nulos,
            open(
                caminho_entrega_nula_nao_cancelada,
                "w",
                encoding="utf-8",
                newline="",
            ) as nao_cancelados,
        ):
            escritor_saida = csv.DictWriter(saida, fieldnames=fieldnames)
            escritor_nulos = csv.DictWriter(nulos, fieldnames=fieldnames)
            escritor_nao_cancelados = csv.DictWriter(
                nao_cancelados,
                fieldnames=fieldnames,
            )

            escritor_saida.writeheader()
            escritor_nulos.writeheader()
            escritor_nao_cancelados.writeheader()

            for linha in leitor:
                estatisticas["total_pedidos"] += 1

                status = str(linha.get("order_status", "")).strip().lower()
                data_entrega = linha.get("order_delivered_customer_date", "")
                data_aprovacao = linha.get("order_approved_at", "")

                # Contagem manual de cancelamentos.
                if status == "canceled":
                    estatisticas["pedidos_cancelados"] += 1

                # Formatação da data de aprovação.
                if not valor_ausente(data_aprovacao):
                    data_formatada = formatar_data_brasileira(data_aprovacao)

                    if data_formatada != data_aprovacao:
                        estatisticas["datas_aprovacao_formatadas"] += 1

                    linha["order_approved_at"] = data_formatada

                # Validação da regra de negócio usando if / elif / else.
                if valor_ausente(data_entrega) and status == "canceled":
                    estatisticas["entregas_nulas"] += 1
                    estatisticas["entregas_nulas_canceladas"] += 1
                    escritor_nulos.writerow(linha)

                elif valor_ausente(data_entrega) and status != "canceled":
                    estatisticas["entregas_nulas"] += 1
                    estatisticas["entregas_nulas_nao_canceladas"] += 1
                    escritor_nulos.writerow(linha)
                    escritor_nao_cancelados.writerow(linha)

                else:
                    # Pedido possui data de entrega preenchida.
                    pass

                escritor_saida.writerow(linha)

    estatisticas["hipotese_confirmada"] = (
        estatisticas["entregas_nulas"] > 0
        and estatisticas["entregas_nulas_nao_canceladas"] == 0
    )

    return estatisticas


def exibir_relatorio(estat_produtos, estat_pedidos):
    """
    Exibe o sumário estatístico final construído manualmente.
    """
    print("\n" + "=" * 68)
    print("RELATÓRIO FINAL - PIPELINE DE SANITIZAÇÃO OLIST")
    print("=" * 68)

    print("\nPRODUTOS")
    print("-" * 68)
    print(f"Total de produtos processados: {estat_produtos['total_produtos']}")
    print(
        "Categorias nulas corrigidas: "
        f"{estat_produtos['categorias_corrigidas']}"
    )
    print(
        "Dimensões físicas corrigidas: "
        f"{estat_produtos['dimensoes_corrigidas']}"
    )
    print(
        "Total de valores nulos corrigidos nos produtos: "
        f"{estat_produtos['total_nulos_corrigidos']}"
    )

    print("\nMédias utilizadas para imputação:")
    for coluna, media in estat_produtos["medias_dimensoes"].items():
        print(f"  - {coluna}: {media:.2f}")

    print("\nPEDIDOS")
    print("-" * 68)
    print(f"Total de pedidos processados: {estat_pedidos['total_pedidos']}")
    print(
        "Total de pedidos cancelados identificados: "
        f"{estat_pedidos['pedidos_cancelados']}"
    )
    print(
        "Pedidos com data de entrega nula: "
        f"{estat_pedidos['entregas_nulas']}"
    )
    print(
        "Entrega nula + status canceled: "
        f"{estat_pedidos['entregas_nulas_canceladas']}"
    )
    print(
        "Entrega nula + status diferente de canceled: "
        f"{estat_pedidos['entregas_nulas_nao_canceladas']}"
    )
    print(
        "Datas de aprovação formatadas: "
        f"{estat_pedidos['datas_aprovacao_formatadas']}"
    )

    print("\nVALIDAÇÃO DA HIPÓTESE DE NEGÓCIO")
    print("-" * 68)

    if estat_pedidos["entregas_nulas"] == 0:
        print(
            "Não foram encontrados pedidos com data de entrega nula; "
            "portanto, não há casos suficientes para testar a hipótese."
        )
    elif estat_pedidos["hipotese_confirmada"]:
        print(
            "HIPÓTESE CONFIRMADA: todos os pedidos com "
            "order_delivered_customer_date vazia estão cancelados."
        )
    else:
        print(
            "HIPÓTESE REFUTADA: existem pedidos com "
            "order_delivered_customer_date vazia cujo status NÃO é canceled."
        )
        print(
            "Consulte o arquivo "
            "'orders_entrega_nula_nao_cancelados.csv' para comprovação."
        )

    print("\nArquivos sanitizados foram gravados na pasta 'saida'.")
    print("=" * 68)


def validar_arquivos():
    """
    Verifica se os dois CSVs de entrada existem antes do processamento.
    """
    arquivos = [ARQUIVO_PRODUTOS, ARQUIVO_PEDIDOS]
    indice = 0

    # Uso proposital de while para demonstrar também essa estrutura
    # de repetição pedida no projeto.
    while indice < len(arquivos):
        if not arquivos[indice].exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {arquivos[indice]}\n"
                "Coloque os dois CSVs na mesma pasta do main.py."
            )

        indice += 1


def main():
    validar_arquivos()

    PASTA_SAIDA.mkdir(exist_ok=True)

    produtos_saida = PASTA_SAIDA / "olist_products_sanitizado.csv"
    pedidos_saida = PASTA_SAIDA / "olist_orders_sanitizado.csv"
    pedidos_entrega_nula = PASTA_SAIDA / "orders_entrega_nula.csv"
    pedidos_nulos_nao_cancelados = (
        PASTA_SAIDA / "orders_entrega_nula_nao_cancelados.csv"
    )

    estat_produtos = sanitizar_produtos(
        ARQUIVO_PRODUTOS,
        produtos_saida,
    )

    estat_pedidos = processar_pedidos(
        ARQUIVO_PEDIDOS,
        pedidos_saida,
        pedidos_entrega_nula,
        pedidos_nulos_nao_cancelados,
    )

    exibir_relatorio(estat_produtos, estat_pedidos)


if __name__ == "__main__":
    main()
