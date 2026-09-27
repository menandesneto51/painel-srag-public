# Execução v2.3 no Cursor — Persistência Operacional

## Objetivo

Comparar filas de revisão entre snapshots agregados e distinguir mudanças no fluxo de trabalho sem interpretar persistência como gravidade.

## Pré-requisito

Executar primeiro a v2.2:

```bash
python scripts/run_v2_2_pipeline.py
```

Arquivo necessário:

`data_candidate/operational_v2_2/municipal_review_queue_v2_2.csv`

## Primeiro vintage

```bash
python scripts/capture_operational_vintage.py
```

O primeiro snapshot serve apenas como baseline.

## Vintages seguintes

A cada nova execução validada da v2.2:

```bash
python scripts/capture_operational_vintage.py
```

## Comparação

```bash
python scripts/compare_operational_vintages.py \
  --previous data_candidate/operational_vintages/<anterior>/municipal_review_queue_v2_2.csv \
  --current data_candidate/operational_vintages/<atual>/municipal_review_queue_v2_2.csv
```

Saídas:

- `data_candidate/operational_persistence/operational_persistence_v2_3.csv`;
- `operational_persistence_summary_v2_3.csv`;
- `operational_persistence_report_v2_3.md`.

## Estados

- `baseline_snapshot_nonroutine`;
- `baseline_snapshot_routine`;
- `entered_review`;
- `persistent_same_queue`;
- `changed_review_queue`;
- `returned_to_routine`;
- `routine_stable`.

## Interpretação

Esses estados descrevem **mudança de workflow**.

Não significam:

- aumento de risco;
- piora clínica;
- prioridade assistencial;
- urgência;
- necessidade automática de intervenção.

## Revisão visual

```bash
streamlit run app_review_streamlit.py
```

Usar a aba **Persistência v2.3**.

## Proteções

Sempre exigir:

- `change_state_is_not_risk = true`;
- `persistence_is_not_severity = true`;
- `automatic_action_enabled = false`;
- `human_review_required = true`.

## Agentes

Na comparação entre vintages, rodar:

1. DATA-QA — confirmar completude dos 142 municípios;
2. EPIDEMIOLOGIA — revisar mudanças de sinal;
3. TERRITORIAL — identificar padrões regionais;
4. OPERACIONAL — verificar continuidade da fila;
5. PRIVACIDADE — confirmar uso apenas de agregados;
6. DOCUMENTACAO — registrar interpretação e limitações.

## Critério de saída

Após pelo menos dois vintages:

- relatório de entrada/persistência/mudança/retorno à rotina;
- revisão humana dos municípios que mudaram de fila;
- documentação de falsos alarmes de workflow;
- decisão sobre janela mínima de persistência para uso operacional futuro.

Nenhum resultado v2.3 é promovido automaticamente para o painel público.
