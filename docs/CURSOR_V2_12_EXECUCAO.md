# Execução v2.12 no Cursor — Deploy Humano e Verificação de Efeito

## Objetivo

Registrar de forma auditável:

1. decisão humana de realizar deploy;
2. evidência de que o deploy realmente ocorreu;
3. verificação posterior do comportamento da implementação.

A v2.12 não executa deploy, rollback ou alteração automática de regra.

## Pré-requisito

Executar e validar a v2.11:

```bash
python scripts/create_human_merge_decision_template_v2_11.py
python scripts/validate_human_merge_decision_v2_11.py --input CAMINHO/decisao_merge.csv
python scripts/create_post_merge_template_v2_11.py
python scripts/validate_post_merge_v2_11.py --input CAMINHO/post_merge.csv
```

Somente registros:

`post_merge_state = verified_healthy`

podem seguir.

## 1. Gerar decisão de deploy

```bash
python scripts/create_human_deploy_decision_template_v2_12.py
```

Preencher apenas decisões realmente tomadas:

- decided_at;
- reviewer_role;
- deploy_decision;
- decision_rationale.

Valores de deploy_decision:

- approve_human_deploy;
- reject_deploy;
- defer_deploy.

## 2. Validar decisão

```bash
python scripts/validate_human_deploy_decision_v2_12.py \
  --input CAMINHO/deploy_decisions.csv
```

A decisão continua distinta da execução.

## 3. Gerar template de deploy

```bash
python scripts/create_deployment_record_template_v2_12.py
```

Somente decisões `approve_human_deploy` aparecem.

## 4. Registrar deploy real

Preencher:

- deployed_at;
- reviewer_role;
- environment;
- deployed_commit_sha;
- deploy_evidence_ref;
- post_deploy_ci_status;
- smoke_test_status;
- health_check_status;
- security_privacy_check_status;
- rollback_readiness_status;
- deployment_state;
- deployment_notes.

O commit implantado deve ser exatamente o commit mergeado de origem.

## 5. Validar deploy

```bash
python scripts/validate_deployment_record_v2_12.py \
  --input CAMINHO/deployment_record.csv
```

## 6. Gerar template de verificação de efeito

```bash
python scripts/create_effect_verification_template_v2_12.py
```

## 7. Registrar janela observacional

Preencher:

- measured_at;
- reviewer_role;
- observation_window_start;
- observation_window_end;
- effect_state;
- expected_behavior_summary;
- observed_behavior_summary;
- evidence_refs;
- effect_review_notes.

Estados:

- implementation_behavior_verified;
- no_material_behavior_change;
- unexpected_behavior_needs_review;
- insufficient_observation_window.

## 8. Validar efeito

```bash
python scripts/validate_effect_verification_v2_12.py \
  --input CAMINHO/effect_verification.csv
```

Regra obrigatória:

`effect_verification_is_not_causal_inference = true`

## 9. Gerar relatório estadual

```bash
python scripts/build_deployment_verification_report_v2_12.py
```

Saídas:

- deployment_verification_summary_v2_12.json;
- deployment_verification_report_v2_12.md.

## 10. Revisão visual

```bash
streamlit run app_review_streamlit.py
```

Usar a aba **Deploy e efeito v2.12**.

## Agentes

Executar:

1. GATE-DE-MERGE;
2. POS-MERGE;
3. POS-DEPLOY;
4. PRIVACIDADE;
5. AUDITORIA;
6. DOCUMENTACAO.

## Travas

Sempre:

- decisão de deploy != execução;
- deploy exige evidência real;
- deploy != verificação de efeito;
- verificação de efeito != inferência causal;
- automatic_deploy=false;
- automatic_rollback=false;
- automatic_rule_change=false;
- patient_level_decision=false;
- identificadores pessoais do revisor não são armazenados;
- promoção pública automática=false.
