# Execução v2.8 no Cursor — Avaliação Formal de Propostas

## Objetivo

Avaliar formalmente propostas v2.7 e decidir se podem seguir para uma branch de implementação.

## Pré-requisitos

Executar v2.7:

    python scripts/build_rule_change_proposals_v2_7.py

Quando aplicável, executar também shadow mode:

    python scripts/build_candidate_review_queue_v2_7.py --proposal-id PROP_ID --candidate-rule-version candidate-001 --candidate-config CAMINHO/candidate_operational_review.json
    python scripts/evaluate_rule_change_shadow_v2_7.py --proposal-id PROP_ID --candidate-queue data_candidate/rule_shadow_evaluation_v2_7/PROP_ID/candidate_review_queue_v2_7.csv --candidate-rule-version candidate-001

## 1. Gerar template formal

    python scripts/create_rule_change_evaluation_template_v2_8.py

Saída:

data_candidate/rule_change_evaluation_v2_8/rule_change_evaluation_template_v2_8.csv

## 2. Preencher avaliação humana

Preencher:

- evaluated_at
- reviewer_role
- case_review_status
- case_review_refs
- epidemiology_review_status
- epidemiology_review_refs
- shadow_review_status
- shadow_review_refs
- backtest_status
- backtest_refs
- statistical_review_status
- statistical_review_refs
- documentation_status
- documentation_refs
- impact_summary
- risk_summary
- final_decision
- decision_rationale
- implementation_notes

Não inserir identificadores pessoais.

## 3. Validar avaliação

    python scripts/validate_rule_change_evaluation_v2_8.py --input CAMINHO/avaliacoes_preenchidas.csv

Saída:

data_candidate/rule_change_evaluation_v2_8/rule_change_evaluations_validated_v2_8.csv

## 4. Gerar relatório

    python scripts/build_rule_change_evaluation_report_v2_8.py

## 5. Revisão visual

    streamlit run app_review_streamlit.py

Usar a aba Avaliação formal v2.8.

## Gate de aprovação

Para mudanças de lógica, `approve_for_implementation_branch` só é válido quando:

- case review = passed
- epidemiology review = passed
- shadow review = passed, com evidência v2.7 da mesma proposal_id
- backtest = passed
- statistical review = passed
- documentation = passed

## Agentes no Cursor

Executar:

1. AGENTE-CONTROLE-DE-MUDANCAS
2. DATA-QA
3. EPIDEMIOLOGIA
4. ESTATISTICA
5. PRIVACIDADE
6. DOCUMENTACAO

## Regras obrigatórias

- decision_is_not_implementation=true
- automatic_rule_change_enabled=false
- automatic_threshold_change_enabled=false
- automatic_merge_enabled=false
- automatic_deploy_enabled=false
- human_approval_required=true
- personal_identifier_storage=false

Uma decisão aprovada autoriza apenas a criação/preparação de uma branch separada.


## Gate adicional de elegibilidade

Para `approve_for_implementation_branch` em mudança lógica:

- proposal_status=ready_for_human_decision
- shadow_review_status=passed
- arquivo `rule_shadow_evaluation_summary_v2_7.json` da mesma proposal_id presente
- shadow_only=true
- automatic_activation=false
- candidate_rule_activated=false

O validador v2.8 lê a evidência shadow em:

`data_candidate/rule_shadow_evaluation_v2_7/<proposal_id>/`

Sem essa evidência, a aprovação é bloqueada.
