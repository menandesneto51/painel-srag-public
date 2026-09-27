# v2.6 — Concordância entre Workflow e Decisão Humana

## Objetivo

Usar decisões humanas acumuladas para revisar **regras do sistema**, não para pontuar revisores.

A pergunta é:

> A fila/recomendação técnica está coerente com o fluxo de decisão adotado pelos revisores humanos?

Não é:

> O humano acertou ou errou?

## Princípio

A decisão humana é a autoridade final do workflow institucional, mas **não é padrão-ouro epidemiológico**.

Discordância serve para revisar:

- regras de fila;
- gatilhos;
- matriz de ações;
- thresholds;
- documentação;
- necessidade de contexto adicional.

## Classes iniciais

- `nonroutine_escalation_aligned`;
- `routine_non_escalation_aligned`;
- `routine_escalated_rule_review`;
- `nonroutine_not_escalated_rule_review`;
- `decision_outside_alignment_map`.

As classes com `rule_review` apontam regra/processo a revisar. Não apontam erro humano.

## Contexto adicional

Quando disponível, a v2.6 incorpora:

- estabilidade operacional v2.4;
- estado de follow-up v2.5.

Isso permite responder, por exemplo:

- filas não rotineiras persistentes que repetidamente terminam sem escalonamento;
- casos inicialmente rotineiros que exigem escalonamento humano;
- regras com alta discordância em determinados contextos.

## Proteções

Sempre:

- `human_decision_is_epidemiological_gold_standard=false`;
- `reviewer_score_enabled=false`;
- `municipality_rank_enabled=false`;
- `automatic_rule_change_enabled=false`;
- `automatic_execution_enabled=false`.

Nenhuma regra é alterada automaticamente com base na discordância.
