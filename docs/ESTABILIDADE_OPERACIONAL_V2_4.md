# v2.4 — Estabilidade Operacional

## Objetivo

Analisar múltiplos vintages da fila v2.2 para distinguir padrões persistentes de mudanças transitórias do workflow.

## Conceitos separados

A v2.4 não substitui:

- estabilidade epidemiológica por atraso de notificação;
- baseline/anomalia;
- risco clínico;
- pressão assistencial.

Ela mede apenas **estabilidade da fila de revisão**.

## Janela inicial

Configuração padrão:

- últimos 4 vintages;
- persistência mínima: 2 ciclos;
- sustentação: 3 ciclos.

Esses parâmetros são experimentais e deverão ser avaliados depois de acumular vintages reais.

## Métricas por município

- vintages_observed;
- distinct_review_queues;
- nonroutine_cycles;
- nonroutine_fraction;
- current_nonroutine_run;
- longest_nonroutine_run;
- current_same_queue_run;
- queue_change_count;
- workflow_churn_rate;
- single_cycle_reversion_count.

## Padrões

- insufficient_history;
- routine_stable;
- newly_entered_review;
- single_cycle_reversion;
- persistent_same_queue;
- persistent_nonroutine_changed_queue;
- recently_returned_to_routine;
- oscillating_workflow;
- mixed_workflow_history.

## Proteções

Sempre:

- `workflow_stability_is_not_risk = true`;
- `persistence_is_not_severity = true`;
- `transience_is_not_reassurance = true`;
- `automatic_action_enabled = false`;
- `human_review_required = true`.

Uma reversão de um ciclo não prova que o sinal anterior era falso. Da mesma forma, persistência não prova maior gravidade.

## Cursor

Depois de acumular vintages:

```bash
python scripts/analyze_operational_stability.py
```

Saídas:

- `operational_stability_v2_4.csv`;
- `operational_stability_summary_v2_4.csv`;
- `operational_stability_report_v2_4.md`.

## Uso futuro

Após vários ciclos reais, avaliar:

- proporção de entradas que revertem no ciclo seguinte;
- filas com maior churn;
- duração típica de persistência;
- estabilidade por região;
- concordância com decisões humanas registradas;
- necessidade ou não de exigir 2 ciclos antes de determinadas revisões de workflow.

Nenhum limiar de persistência será convertido automaticamente em regra operacional sem avaliação retrospectiva e aprovação humana.
