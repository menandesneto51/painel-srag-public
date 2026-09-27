# Execução v2.14 no Cursor — Post-Mortem e Aprendizado Controlado

## Objetivo

Registrar lições após mudança mantida, revertida ou ainda em investigação, sem alterar automaticamente regra, threshold, deploy ou rollback.

## Fontes

- effect_verification_validated_v2_12.csv;
- rollback_execution_validated_v2_13.csv.

## 1. Gerar template

```bash
python scripts/create_postmortem_template_v2_14.py
```

## 2. Preencher post-mortem

Campos centrais:

- conducted_at;
- reviewer_role;
- postmortem_status;
- outcome_state;
- event_summary;
- expected_behavior_summary;
- observed_behavior_summary;
- contributing_factors;
- safeguards_that_worked;
- safeguards_to_improve;
- lessons_learned;
- learning_action_type;
- follow_up_actions;
- evidence_refs.

## 3. Retorno opcional à revisão de regra

Se houver necessidade real de rever regra:

```text
reenter_rule_review=true
learning_action_type=rule_review
rule_review_scope=<escopo válido>
rule_review_reason=<justificativa>
```

Isso apenas devolve o tema ao fluxo humano. Não altera a regra.

## 4. Validar

```bash
python scripts/validate_postmortem_v2_14.py --input CAMINHO/postmortem.csv
```

## 5. Gerar relatório estadual

```bash
python scripts/build_postmortem_report_v2_14.py
```

## 6. Revisão visual

```bash
streamlit run app_review_streamlit.py
```

Usar a aba **Post-mortem v2.14**.

## Travas

- postmortem_is_not_causal_proof=true;
- learning_is_not_rule_change=true;
- rule_reentry_requires_human_review=true;
- automatic_rule_change=false;
- automatic_issue_creation=false;
- automatic_deploy=false;
- automatic_rollback=false;
- patient_level_decision=false;
- personal_identifier_storage=false.
