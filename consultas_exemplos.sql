-- Consultas de exemplo sobre a tabela `cotacoes` gerada pelo etl_cotacoes.py
-- Rode com: sqlite3 cotacoes.db < consultas_exemplos.sql

-- 1. Última cotação registrada de cada moeda
SELECT par, compra, venda, data_hora
FROM cotacoes
WHERE (par, data_hora) IN (
    SELECT par, MAX(data_hora)
    FROM cotacoes
    GROUP BY par
);

-- 2. Spread (diferença entre venda e compra) por moeda
SELECT
    par,
    ROUND(venda - compra, 4) AS spread,
    ROUND((venda - compra) / compra * 100, 2) AS spread_pct
FROM cotacoes;

-- 3. Histórico de variação percentual por moeda, ordenado do mais recente
SELECT par, variacao_pct, data_hora
FROM cotacoes
ORDER BY data_hora DESC, par;

-- 4. Média de cotação de compra por moeda (útil quando o pipeline já rodou
--    várias vezes e o histórico tem mais de um registro por par)
SELECT par, ROUND(AVG(compra), 4) AS compra_media
FROM cotacoes
GROUP BY par;
