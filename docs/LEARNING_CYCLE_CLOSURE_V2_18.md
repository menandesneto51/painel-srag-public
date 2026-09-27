# v2.18 — Gate Humano de Encerramento do Ciclo de Aprendizado

## Objetivo

Separar o fechamento documental do post-mortem v2.14 do encerramento efetivo do ciclo de aprendizado.

`postmortem_status=closed` não implica `learning_cycle_closed_human`.

## Pré-condições para close_learning_cycle

- post-mortem v2.14 fechado e válido;
- ao menos uma ação v2.17;
- todas as ações em estado terminal (`verified_closed` ou `cancelled`);
- revisão de cobertura das ações = passed;
- revisão das evidências = passed;
- `closure_evidence_refs` não vazio;
- para `rule_review`, handoff de governança presente e revisado.

## Estados

- `learning_cycle_closed_human`;
- `learning_cycle_open`;
- `learning_cycle_closure_deferred`.

## Proteções

- `postmortem_closed_is_not_learning_cycle_closed=true`;
- `closure_is_not_epidemiological_effect=true`;
- `closure_does_not_change_source_records=true`;
- `human_closure_required=true`;
- `automatic_closure=false`;
- `automatic_issue_creation=false`;
- `automatic_rule_change=false`;
- `automatic_deploy=false`;
- `automatic_rollback=false`;
- `personal_identifier_storage=false`.

## Natureza

O fechamento v2.18 é uma decisão humana de governança. Ele não altera o post-mortem, as ações de follow-up, regras, thresholds, deploys ou rollbacks.
