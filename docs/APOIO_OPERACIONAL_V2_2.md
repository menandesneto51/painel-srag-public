# v2.2 — Apoio Operacional Explicável

## Finalidade

A v2.2 organiza o trabalho de revisão sobre a inteligência territorial v2.1.

Ela **não** cria ranking de risco, não decide ações de saúde automaticamente e não substitui decisão humana.

## Entrada

Cards explicáveis v2.1:

`territorial_review_cards_v2_1.csv`

## Saída principal

Cada município recebe uma **fila de revisão**, que representa o tipo de trabalho necessário.

Filas iniciais:

- data_validation_first;
- targeted_silence_verification;
- multidisciplinary_review;
- epidemiology_virology_review;
- epidemiology_review;
- laboratory_review;
- routine_monitoring.

A ordem acima não representa gravidade.

## Matriz de ações

Cada `review_tag` possui ações sugeridas de verificação.

Exemplo:

`data_quality_review`

gera tarefas de revisar:

- oportunidade;
- completude;
- inconsistências;
- registros sem desfecho.

As ações são sugestões para revisão humana. Nenhuma ação é executada pelo sistema.

## Relatório estadual

A v2.2 gera um relatório com:

- quantidade de municípios por fila;
- municípios em cada fila;
- mensagem explícita de que a fila não é ranking de risco.

## Princípios de segurança/governança

Sempre:

- `human_review_required = true`;
- `automatic_execution_enabled = false`;
- `patient_level_decision_enabled = false`;
- `composite_score_used = false`;
- `queue_is_not_risk_rank = true`.

## Cursor

A matriz é versionada em:

`config/operational_review_v2_2.json`

Mudanças de regra exigem:

- documentação;
- teste;
- comparação com comportamento anterior;
- revisão epidemiológica;
- aprovação humana antes de uso institucional.
