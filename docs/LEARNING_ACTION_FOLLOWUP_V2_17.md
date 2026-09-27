# v2.17 — Follow-up Auditável das Ações de Aprendizado

## Objetivo

Transformar as ações de acompanhamento registradas no post-mortem v2.14 em registros estruturados de execução declarada, prazo, evidência e verificação humana.

A v2.17 não executa ações e não mede efetividade epidemiológica.

## Fonte

Somente post-mortems v2.14 com status `in_review` ou `closed` e `learning_action_type != none` podem originar ações.

## Estados da ação

- `planned`;
- `acknowledged`;
- `in_progress`;
- `blocked`;
- `completed`;
- `cancelled`.

## Verificação humana

Ações concluídas exigem evidência. O estado `completed` pode ficar `pending`, `verified` ou `rejected`.

`verified_closed` significa que a evidência de conclusão foi conferida por humano. Não significa que a ação produziu efeito epidemiológico.

## Prazo

`overdue` é derivado com `as_of` explícito e timezone.

`overdue_is_not_risk=true`

## Rule review

Quando a ação de origem é `rule_review`, uma conclusão exige `governance_handoff_ref`. Esse campo documenta o handoff humano; ele não cria issue, PR, regra ou threshold.

## Privacidade

Somente papéis (`owner_role`, `verifier_role`) são armazenados. Identificadores pessoais não devem ser incluídos.

## Proteções

- `tracking_is_not_execution=true`;
- `completion_is_not_effectiveness_proof=true`;
- `verification_is_not_epidemiological_effect=true`;
- `overdue_is_not_risk=true`;
- `human_verification_required=true`;
- `automatic_execution=false`;
- `automatic_issue_creation=false`;
- `automatic_rule_change=false`;
- `personal_identifier_storage=false`.

## Saídas

- `learning_action_followup_validated_v2_17.csv`;
- `learning_action_followup_summary_v2_17.json`;
- `learning_action_followup_report_v2_17.md`.
