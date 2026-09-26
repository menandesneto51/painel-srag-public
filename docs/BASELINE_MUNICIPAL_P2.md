# Baseline Municipal Histórico — P2

## Regra territorial

O baseline municipal por contagem pode preencher semanas sem casos com zero **somente quando o município era territorialmente válido no ano analisado**.

A configuração está em:

`config/municipality_harmonization.json`

## Boa Esperança do Norte

O IBGE informa instalação oficial em **1º de janeiro de 2025**.

Consequências:

- 2019–2024: não criar linhas zero para Boa Esperança do Norte;
- 2025 em diante: município pode integrar a matriz;
- não reconstruir retrospectivamente casos de municípios predecessores sem metodologia específica.

Fontes de referência:

- IBGE — atualização das estruturas territoriais;
- IBGE Educa — novo município Boa Esperança do Norte.

## Sem taxas históricas ainda

O baseline municipal inicial usa **contagens**.

Taxas históricas permanecem bloqueadas até incorporar:

- população anual por município;
- harmonização territorial por ano;
- tratamento específico de Boa Esperança do Norte e territórios de origem.

## Saídas

```bash
python scripts/build_historical_municipal_baseline.py \
  --baseline-years 2023,2024,2025
```

Produz:

- `historical_weekly_municipal_mt.csv`;
- `baseline_casos_municipal_mt.csv`;
- `historical_municipal_metadata.json`.

## Interpretação

Cada linha de baseline informa `n_years`.

Um município recém-instalado pode ter menos de três anos disponíveis mesmo quando o baseline solicitado inclui três ou mais anos. Os módulos de anomalia/silêncio devem respeitar esse número e retornar `insufficient_baseline` quando necessário.
