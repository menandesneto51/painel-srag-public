# Execução v2.6 no Cursor — Concordância Workflow × Decisão Humana

## Objetivo

Usar decisões humanas acumuladas para identificar regras do workflow que merecem revisão.

A v2.6 não avalia desempenho individual de revisores e não usa decisão humana como padrão-ouro epidemiológico.

## Pré-requisitos

Executar e possuir artefatos da v2.4 e v2.5:

    python scripts/analyze_operational_stability.py
    python scripts/create_decision_audit_template_v2_5.py
    python scripts/validate_decision_audit_v2_5.py --input CAMINHO_SEGURO/decisoes.csv

Opcionalmente:

    python scripts/validate_follow_up_v2_5.py --events CAMINHO_SEGURO/follow_up.csv --as-of <DATA_HORA>

## Executar concordância

    python scripts/build_human_workflow_concordance_v2_6.py

Saídas:

- data_candidate/human_workflow_concordance_v2_6/human_workflow_concordance_v2_6.csv
- human_workflow_concordance_summary_v2_6.json
- human_workflow_concordance_report_v2_6.md

## Classes

- nonroutine_escalation_aligned
- routine_non_escalation_aligned
- routine_escalated_rule_review
- nonroutine_not_escalated_rule_review
- decision_outside_alignment_map

Classes com rule_review são candidatas à revisão da regra/processo, não indicação de erro humano.

## Contextos incorporados

Quando disponíveis, a v2.6 adiciona:

- workflow_pattern da v2.4
- current_nonroutine_run
- current_same_queue_run
- follow_up_state da v2.5

## Revisão visual

    streamlit run app_review_streamlit.py

Usar a aba **Concordância workflow × decisão v2.6**.

## Agentes no Cursor

Executar:

1. DATA-QA
2. EPIDEMIOLOGIA
3. OPERACIONAL
4. ESTATISTICA
5. PRIVACIDADE
6. AUDITORIA
7. GOVERNANCA-DE-REGRAS
8. DOCUMENTACAO

## Regras obrigatórias

- human_decision_is_epidemiological_gold_standard=false
- reviewer_score_enabled=false
- municipality_rank_enabled=false
- automatic_rule_change_enabled=false
- automatic_execution_enabled=false

Discordância não significa erro humano.

Concordância não prova correção epidemiológica da regra.

## Critério de saída

Depois de acumular decisões reais:

- identificar filas com maior frequência de rule_review_required
- revisar casos de rotina que exigiram escalonamento humano
- revisar filas não rotineiras frequentemente encerradas sem escalonamento
- estratificar achados por estabilidade v2.4
- revisar influência de follow-ups vencidos ou concluídos
- propor alteração de regra somente com análise de casos, documentação, teste retrospectivo e aprovação humana

Nenhuma regra é reescrita automaticamente.

## Proteção adicional

- promoção/publicação automática = false
- alteração de threshold automática = false
- alteração de regra automática = false
- qualquer proposta deve ser registrada, backtestada e aprovada por revisão humana
