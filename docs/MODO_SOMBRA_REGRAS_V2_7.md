# v2.7 — Avaliação de Regra Candidata em Modo Sombra

## Objetivo

Avaliar uma regra candidata sem ativá-la.

A fila candidata deve ser produzida separadamente, em ambiente de desenvolvimento/Cursor, e entregue ao avaliador como CSV agregado de 142 municípios.

O avaliador **não executa a proposta** e **não reescreve configuração**.

## Entradas

- registro de propostas v2.7;
- fila atual v2.2;
- fila candidata;
- decisões humanas v2.5, quando disponíveis;
- configuração de concordância v2.6.

## Execução

```bash
python scripts/evaluate_rule_change_shadow_v2_7.py \
  --proposal-id PROP_ID \
  --candidate-queue CAMINHO/fila_candidata.csv \
  --candidate-rule-version candidate-001
```

## Saídas

Diretório por proposta:

`data_candidate/rule_shadow_evaluation_v2_7/<proposal_id>/`

Arquivos:

- `rule_shadow_evaluation_v2_7.csv`;
- `rule_shadow_evaluation_summary_v2_7.json`;
- `rule_shadow_evaluation_report_v2_7.md`.

## O que é medido

- municípios que mudariam de fila;
- transições de fila;
- concordância atual com decisões humanas;
- concordância candidata com decisões humanas;
- mudança de concordância do workflow.

## O que não é medido

A concordância com decisão humana não é acurácia epidemiológica.

Portanto:

- `workflow_agreement_improved` não prova melhor detecção epidemiológica;
- `workflow_agreement_worsened` não prova que a regra candidata seja epidemiologicamente pior;
- decisão humana não é padrão-ouro epidemiológico.

## Gate

Mesmo após resultado favorável em modo sombra:

- regra não é ativada;
- threshold não é alterado;
- proposta não muda automaticamente para approved;
- é obrigatória revisão de casos;
- é obrigatório backtesting adequado ao tipo de mudança;
- é necessária revisão epidemiológica/estatística;
- é necessária aprovação humana.

## Proteções

Sempre:

- `shadow_only=true`;
- `automatic_activation=false`;
- `automatic_rule_change=false`;
- `reviewer_scoring=false`;
- `municipality_ranking=false`;
- `human_decision_is_epidemiological_gold_standard=false`.
