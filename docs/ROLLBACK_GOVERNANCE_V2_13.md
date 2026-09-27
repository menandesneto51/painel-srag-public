# v2.13 — Rollback Humano e Verificação Pós-Rollback

## Objetivo

Registrar de forma segura e auditável:

1. decisão humana de considerar rollback;
2. aprovação/rejeição/adiamento;
3. rollback realmente executado;
4. verificação pós-rollback.

A v2.13 não executa rollback automaticamente.

## Fontes elegíveis

A decisão pode partir de:

- deployment_state=rollback_consideration;
- effect_state=unexpected_behavior_needs_review.

Um efeito inesperado permanece uma evidência operacional/técnica e não uma inferência causal epidemiológica.

## Decisão

Estados:

- approve_human_rollback;
- reject_rollback;
- defer_rollback.

É obrigatório definir:

- rollback_target_commit_sha;
- rollback_plan_ref;
- rationale;
- reviewer_role.

O alvo deve ser diferente do commit atualmente implantado.

## Execução

Somente approve_human_rollback pode originar registro de execução.

O commit efetivamente restaurado deve ser exatamente o alvo aprovado.

Estados:

- verified_restored;
- needs_investigation.

verified_restored exige:

- CI pós-rollback=passed;
- smoke test=passed;
- health check=passed;
- segurança/privacidade=passed;
- sanity epidemiológico=passed.

## Proteções

Sempre:

- rollback_decision_is_not_rollback_execution=true;
- rollback_record_requires_actual_rollback_evidence=true;
- automatic_rollback=false;
- automatic_deploy=false;
- automatic_rule_change=false;
- patient_level_decision=false;
- personal_identifier_storage=false;
- revisão humana obrigatória.
