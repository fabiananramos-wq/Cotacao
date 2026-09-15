# ETL de Cotações de Moedas (USD/EUR → BRL)

Pipeline em Python que busca, transforma e armazena cotações de moedas estrangeiras em relação ao Real, usando uma API pública gratuita. Pensado para times financeiros/produto que precisam de um histórico simples de cotação para conciliação, custo de operação internacional ou dashboards internos.

## Extract → Transform → Load

1. **Extract** — busca a cotação atual de USD-BRL e EUR-BRL na [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas) (API pública e gratuita, sem necessidade de chave). Se a API estiver indisponível, o script usa automaticamente um arquivo de exemplo local (`exemplo_resposta_api.json`), para que a demonstração nunca dependa de uma chamada externa funcionar no momento certo.
2. **Transform** — normaliza o JSON da API em linhas tabulares: par de moeda, cotação de compra e venda, variação percentual e data/hora da cotação.
3. **Load** — grava os dados em um banco SQLite (`cotacoes.db`), com uma constraint de unicidade (moeda + data/hora) para que rodar o script várias vezes não duplique dados — comportamento essencial em qualquer pipeline de dados que roda periodicamente.

## Como rodar

```bash
pip install requests
python etl_cotacoes.py            # tenta buscar dado real da API
python etl_cotacoes.py --offline  # força uso do arquivo de exemplo local
```

Depois de rodar, consulte os dados com os exemplos em `consultas_exemplos.sql`:

```bash
sqlite3 cotacoes.db < consultas_exemplos.sql
```

## Por que este projeto

Combina três coisas que aparecem constantemente em trabalho PJ de dados/automação: consumo de API externa, tratamento de falha (a API pode cair, mudar formato ou ficar lenta) e modelagem simples em banco relacional. O recorte em dados financeiros também é proposital — é a área onde tenho profundidade real, vinda da minha experiência em produtos de pagamento.

## Possíveis evoluções

- Agendar a execução periódica (ex: cron job ou GitHub Actions) para construir um histórico real ao longo do tempo.
- Adicionar mais pares de moeda ou fonte alternativa de cotação.
- Expor os dados via uma API própria simples (FastAPI) ou um dashboard (Streamlit).
