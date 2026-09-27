# Cards Explicáveis de Revisão Territorial — v2.1

## Finalidade

Transformar estados técnicos em um resumo municipal auditável para revisão humana.

Os cards não usam LLM para decidir o conteúdo básico. Eles são derivados por regras determinísticas dos artefatos v2.1.

## Tags possíveis

Exemplos:

- epidemiology_review;
- trend_review;
- data_quality_review;
- insufficient_evidence;
- silence_verification;
- virology_review;
- laboratory_coverage_review;
- healthcare_coordination.

## Proteções

Todo card contém:

- `human_review_required = true`;
- `operational_recommendation_enabled = false`;
- `composite_score_used = false`;
- `card_status = experimental_explainable_review`.

Uma tag não é uma classe de risco nem um alerta.

## Uso no Cursor

Após gerar a inteligência territorial:

```bash
python scripts/build_territorial_review_cards.py
```

Saída:

`data_candidate/territorial_intelligence/territorial_review_cards_v2_1.csv`
