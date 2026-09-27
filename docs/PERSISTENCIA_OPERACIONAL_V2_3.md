# v2.3 — Persistência das Filas de Revisão

## Objetivo

Comparar a fila operacional entre snapshots agregados e distinguir:

- entrada em revisão;
- persistência na mesma fila;
- mudança de fila;
- retorno ao monitoramento de rotina;
- rotina estável.

## Regra central

Persistência **não é gravidade**.

Mudança de fila **não é aumento/redução de risco**.

A v2.3 serve para reduzir interpretação reativa de um único snapshot e organizar a continuidade da revisão humana.

## Captura de vintage

Depois da v2.2:

```bash
python scripts/capture_operational_vintage.py
```

Saída local:

`data_candidate/operational_vintages/<snapshot_id>/`

Somente agregados municipais são capturados.

## Comparação

```bash
python scripts/compare_operational_vintages.py \
  --previous data_candidate/operational_vintages/<anterior>/municipal_review_queue_v2_2.csv \
  --current data_candidate/operational_vintages/<atual>/municipal_review_queue_v2_2.csv
```

Saídas:

- `operational_persistence_v2_3.csv`;
- `operational_persistence_summary_v2_3.csv`;
- `operational_persistence_report_v2_3.md`.

## Estados

- baseline_snapshot_nonroutine;
- baseline_snapshot_routine;
- entered_review;
- persistent_same_queue;
- changed_review_queue;
- returned_to_routine;
- routine_stable.

## Proteções

Sempre:

- `change_state_is_not_risk = true`;
- `persistence_is_not_severity = true`;
- `automatic_action_enabled = false`;
- `human_review_required = true`.

Não existe ranking, score composto ou alerta automático.
