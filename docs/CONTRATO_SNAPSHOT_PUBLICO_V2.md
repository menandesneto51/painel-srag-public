# Contrato do Snapshot Público v2

## Objetivo

Transformar os artefatos produzidos no ambiente de processamento em um conjunto público pequeno, auditável e seguro.

## Builder

```bash
python scripts/build_public_snapshot_v2.py
```

Origem padrão:

`data_candidate/`

Destino:

`data_candidate/public_snapshot/`

## Arquivos obrigatórios

- `metadata_public.json`
- `kpis.json`
- `weekly_summary.csv`
- `risk_summary.csv`
- `risk_summary_v2_candidate.csv`
- `silent_summary.csv`
- `virology_summary.csv`
- `forecast_summary.csv`
- `or_obito_summary.csv`
- `or_uti_summary.csv`

## Regras

### Território

A incidência recente é calculada a partir da série municipal por SE e termina na `stable_week_cases`.

O builder não reutiliza `casos_recentes`, incidências ou score do snapshot legado.

O score v2 permanece:

`under_calibration`

até backtesting e validação.

### Forecast

Se não houver um novo forecast reproduzível, o arquivo é publicado apenas com schema e:

`forecast_status = blocked_not_reprocessed`

Nenhum forecast legado é carregado para o snapshot v2.

### Silêncio epidemiológico

Enquanto a metodologia não for recalibrada, `silent_summary.csv` permanece vazio com schema válido e:

`silence_model_status = blocked_not_recalibrated`

### Odds Ratio

Quando as tabelas brutas v2 existirem, o snapshot preserva:

- OR;
- IC95%;
- quatro células da tabela 2×2;
- N válido;
- missing;
- correção de célula zero;
- identificação do modelo bruto.

### Virologia

O resumo público agrega detecções do pipeline temporal. Coinfecções permanecem possíveis; participação é participação entre detecções, não positividade específica.

## Status inicial

Todo snapshot construído recebe:

`publication_status = under_review`

O builder nunca promove automaticamente dados para `validated`.
