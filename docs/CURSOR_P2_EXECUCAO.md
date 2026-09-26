# Execução P2 no Cursor — Painel SRAG Público

## Objetivo

Executar, em ordem reprodutível:

`SIVEP atual -> qualidade -> histórico -> baseline -> tendência -> anomalia -> confiança -> silêncio`

Todos os resultados do P2 permanecem experimentais até backtesting e validação humana.

## 1. Abrir a branch

```bash
git checkout v2-saneamento-epidemiologico
git pull
```

O Cursor deve obedecer:

- `.cursor/rules/painel-srag-v2.mdc`;
- `docs/AGENTES_E_FLUXO_CURSOR.md`.

## 2. Instalar dependências

```bash
python -m pip install -r requirements.txt
```

## 3. Baixar SIVEP atual

```bash
python scripts/download_official_sources.py --source sivep_gripe_2026
```

## 4. Gerar P1 atual

```bash
python scripts/build_sivep_mt_aggregates.py
python scripts/build_quality_metrics.py
```

Arquivos esperados:

- `data_candidate/municipal_weekly_srag_mt_2026.csv`;
- `data_candidate/sivep_mt_2026_metadata.json`;
- `data_candidate/quality_municipal_sivep_mt_2026.csv`.

## 5. Baixar histórico

```bash
python scripts/download_sivep_history.py
```

Os arquivos brutos permanecem fora do Git.

## 6. Construir painel histórico

```bash
python scripts/build_historical_panel.py
```

Saída:

`data_candidate/history/municipal_weekly_history.csv`

O builder exige:

- 142 municípios;
- semanas epidemiológicas completas;
- zero explícito quando não houver ocorrência;
- chave `ANO + SE + codigo_ibge` única.

## 7. Executar P2

```bash
python scripts/run_p2_pipeline.py
```

O script lê a `stable_week_provisional` do metadata P1 e gera:

- `baseline_seasonal.csv`;
- `anomaly_signals.csv`;
- `trend_signals.csv`;
- `combined_signals.csv`;
- `signal_confidence.csv`;
- `silence_signals.csv`;
- `p2_manifest.json`.

## 8. Regras de interpretação

Não tratar como alerta operacional nenhum registro que contenha:

- `experimental`;
- `under_calibration`;
- `validated_for_operational_alert = false`.

O baseline principal usa inicialmente **hospitalizações em contagem por município**.

Métricas históricas por 100 mil permanecem bloqueadas enquanto não houver denominador populacional do próprio ano.

## 9. Agentes no Cursor

Executar a revisão na ordem:

1. DATA-QA;
2. EPIDEMIOLOGIA;
3. TERRITORIAL;
4. ESTATISTICA;
5. PRIVACIDADE;
6. DOCUMENTACAO.

Gerar relatório de bloqueios antes de qualquer tentativa de promoção.

## 10. Não promover ainda

O P2 não altera automaticamente:

`publication_status = validated`

e não entra em `data_public/` sem:

- backtesting;
- revisão dos agentes;
- aprovação epidemiológica;
- aprovação estatística;
- revisão de privacidade;
- aprovação humana registrada.
