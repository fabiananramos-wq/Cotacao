"""
ETL de Cotações de Moedas (USD/EUR -> BRL)
===========================================

Problema que resolve:
    Times financeiros e produtos de pagamento frequentemente precisam de
    um histórico simples de cotação de moedas para conciliação, análise
    de custo de operação internacional ou dashboards internos — sem
    depender de planilha atualizada manualmente.

O que este pipeline faz (Extract -> Transform -> Load):
    1. EXTRACT — busca a cotação atual de USD-BRL e EUR-BRL na AwesomeAPI
       (API pública e gratuita de cotações: https://docs.awesomeapi.com.br).
       Se a API não responder (sem internet, fora do ar, etc.), o script
       usa automaticamente um arquivo de exemplo local (`exemplo_resposta_api.json`)
       para que o pipeline nunca quebre de forma "silenciosa" em demonstração.
    2. TRANSFORM — normaliza o JSON da API em linhas tabulares
       (moeda, nome, compra, venda, variação, data/hora da cotação).
    3. LOAD — insere os dados em um banco SQLite (`cotacoes.db`),
       evitando duplicar a mesma cotação (moeda + data/hora) se o script
       rodar mais de uma vez.

Como rodar:
    python etl_cotacoes.py            # tenta buscar dado real da API
    python etl_cotacoes.py --offline  # força uso do arquivo de exemplo local

Requisitos:
    pip install requests

Depois de rodar, veja `consultas_exemplos.sql` para exemplos de consulta
sobre os dados carregados.
"""

import argparse
import json
import logging
import sqlite3
from pathlib import Path

import requests

API_URL = "https://economia.awesomeapi.com.br/json/last/USD-BRL,EUR-BRL"
ARQUIVO_EXEMPLO = Path(__file__).parent / "exemplo_resposta_api.json"
BANCO = Path(__file__).parent / "cotacoes.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def extrair(offline: bool = False) -> dict:
    """Busca a cotação na API pública; usa arquivo de exemplo como fallback."""
    if not offline:
        try:
            resposta = requests.get(API_URL, timeout=10)
            resposta.raise_for_status()
            log.info("Cotações obtidas da API em tempo real.")
            return resposta.json()
        except requests.RequestException as erro:
            log.warning("Não foi possível acessar a API (%s). Usando dados de exemplo.", erro)

    with open(ARQUIVO_EXEMPLO, encoding="utf-8") as f:
        log.info("Cotações carregadas do arquivo de exemplo local.")
        return json.load(f)


def transformar(dados_api: dict) -> list[dict]:
    """Converte o JSON da API em uma lista de linhas prontas para o banco."""
    linhas = []
    for par, info in dados_api.items():
        linhas.append(
            {
                "par": par,
                "moeda": info["code"],
                "nome": info["name"],
                "compra": float(info["bid"]),
                "venda": float(info["ask"]),
                "variacao_pct": float(info["pctChange"]),
                "data_hora": info["create_date"],
            }
        )
    return linhas


def carregar(linhas: list[dict], banco: Path) -> int:
    """Insere as linhas no SQLite, evitando duplicar a mesma cotação (par + data_hora)."""
    conexao = sqlite3.connect(banco)
    cursor = conexao.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cotacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            par TEXT NOT NULL,
            moeda TEXT NOT NULL,
            nome TEXT NOT NULL,
            compra REAL NOT NULL,
            venda REAL NOT NULL,
            variacao_pct REAL NOT NULL,
            data_hora TEXT NOT NULL,
            UNIQUE(par, data_hora)
        )
        """
    )

    inseridas = 0
    for linha in linhas:
        try:
            cursor.execute(
                """
                INSERT INTO cotacoes (par, moeda, nome, compra, venda, variacao_pct, data_hora)
                VALUES (:par, :moeda, :nome, :compra, :venda, :variacao_pct, :data_hora)
                """,
                linha,
            )
            inseridas += 1
        except sqlite3.IntegrityError:
            log.info("Cotação de %s em %s já existia no banco — ignorada.", linha["par"], linha["data_hora"])

    conexao.commit()
    conexao.close()
    return inseridas


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL de cotações de moedas (USD/EUR -> BRL)")
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Força o uso do arquivo de exemplo local em vez de chamar a API.",
    )
    args = parser.parse_args()

    log.info("Iniciando pipeline de cotações...")
    dados_api = extrair(offline=args.offline)
    linhas = transformar(dados_api)
    inseridas = carregar(linhas, BANCO)

    log.info("Linhas processadas: %d | Novas linhas inseridas: %d", len(linhas), inseridas)
    log.info("Banco atualizado em: %s", BANCO)
    log.info("Concluído com sucesso.")


if __name__ == "__main__":
    main()
