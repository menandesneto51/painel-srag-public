# v2.7 — Propostas de Mudança de Regra

## Objetivo

Converter padrões de discordância v2.6 em **propostas estruturadas de revisão**, sem alterar automaticamente nenhuma regra.

## Princípio central

Proposta != mudança aplicada.

Toda proposta nasce com:

- proposal_status = draft;
- automatic_rule_change_enabled = false;
- automatic_threshold_change_enabled = false;
- proposal_is_not_change = true;
- human_approval_required = true.

## Origem

A v2.7 usa somente registros v2.6 com:

`rule_review_required = true`

Agrupa-os por:

- regra/fila;
- classe de discordância.

## Tipos de proposta

- queue_rule;
- action_trigger;
- threshold;
- documentation;
- context_requirement.

## Requisitos antes de aprovação

Mudanças de lógica ou threshold exigem:

1. revisão dos casos;
2. revisão epidemiológica;
3. backtesting;
4. revisão estatística quando aplicável;
5. documentação;
6. aprovação humana.

## Proibição

A v2.7 não:

- altera YAML/JSON de produção automaticamente;
- muda thresholds;
- muda fila;
- publica nova regra;
- pontua revisores;
- ranqueia municípios.
