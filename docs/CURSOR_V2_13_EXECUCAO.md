# Execução v2.13 no Cursor — Rollback Humano

## Objetivo

Registrar decisão humana de rollback, evidência de execução e verificação pós-rollback sem automação.

## Pré-requisito

A origem deve ser:

- deployment_state=rollback_consideration; ou
- effect_state=unexpected_behavior_needs_review.

## 1. Gerar template

```bash
python scripts/create_human_rollback_decision_template_v2_13.py
```

## 2. Preencher decisão humana

Campos:

- source_record_type;
- source_record_id;
- decided_at;
- reviewer_role;
- rollback_target_commit_sha;
- rollback_plan_ref;
- rollback_decision;
- decision_rationale.

## 3. Validar decisão

```bash
python scripts/validate_human_rollback_decision_v2_13.py --input CAMINHO/rollback_decisions.csv
```

## 4. Gerar template de execução

```bash
python scripts/create_rollback_execution_template_v2_13.py
```

## 5. Registrar rollback real

Preencher evidência, commit restaurado e checks pós-rollback.

## 6. Validar execução

```bash
python scripts/validate_rollback_execution_v2_13.py --input CAMINHO/rollback_execution.csv
```

## 7. Relatório estadual

```bash
python scripts/build_rollback_report_v2_13.py
```

## 8. Revisão visual

```bash
streamlit run app_review_streamlit.py
```

Usar a aba **Rollback v2.13**.

## Travas

- rollback_decision_is_not_rollback_execution=true;
- rollback_record_requires_actual_rollback_evidence=true;
- automatic_rollback=false;
- automatic_deploy=false;
- automatic_rule_change=false;
- patient_level_decision=false;
- personal_identifier_storage=false.
