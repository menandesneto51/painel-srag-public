# v2.14 — Post-Mortem e Aprendizado Controlado

## Objetivo

Registrar aprendizado institucional após uma mudança mantida, revertida ou ainda em investigação.

A v2.14 não altera regras automaticamente.

## Fontes

O post-mortem pode partir de:

- uma verificação de efeito v2.12;
- uma execução de rollback v2.13.

## O que registrar

- o que ocorreu;
- comportamento esperado;
- comportamento observado;
- fatores contribuintes;
- salvaguardas que funcionaram;
- salvaguardas a melhorar;
- lições aprendidas;
- ações de acompanhamento;
- evidências;
- necessidade ou não de retornar ao ciclo de revisão de regra.

## Linguagem causal

O post-mortem pode documentar fatores contribuintes e evidências.

Ele não deve transformar automaticamente observação temporal em prova causal.

Regra:

`postmortem_is_not_causal_proof=true`

## Retorno ao ciclo de regra

Se `reenter_rule_review=true`:

- learning_action_type deve ser rule_review;
- rule_review_scope é obrigatório;
- rule_review_reason é obrigatório;
- o retorno exige revisão humana;
- nenhuma regra ou threshold é alterado automaticamente.

## Proteções

Sempre:

- learning_is_not_rule_change=true;
- rule_reentry_requires_human_review=true;
- automatic_rule_change=false;
- automatic_issue_creation=false;
- automatic_deploy=false;
- automatic_rollback=false;
- patient_level_decision=false;
- personal_identifier_storage=false.
