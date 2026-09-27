# Execução v2.5 no Cursor — Auditoria Humana e Follow-up

## Objetivo

Registrar decisões humanas sobre a fila/sugestões v2.2 e acompanhar follow-ups sem executar ações automaticamente.

## Pré-requisitos

Executar a v2.2:

    python scripts/run_v2_2_pipeline.py

Arquivos esperados:

- data_candidate/operational_v2_2/municipal_review_queue_v2_2.csv
- data_candidate/operational_v2_2/operational_action_suggestions_v2_2.csv

## 1. Gerar template

    python scripts/create_decision_audit_template_v2_5.py

Saída:

data_candidate/decision_audit_v2_5/human_decision_template_v2_5.csv

## 2. Preenchimento humano

Preencher manualmente:

- decision_scope;
- action_id quando o escopo for action;
- reviewed_at;
- reviewer_role;
- decision_status;
- rationale;
- evidence_refs;
- notes;
- follow_up_required;
- follow_up_due_at quando requerido;
- follow_up_owner_role quando requerido.

Não inserir dados pessoais de pacientes.

## 3. Validar decisões

    python scripts/validate_decision_audit_v2_5.py --input CAMINHO_SEGURO/human_decision_template_preenchido.csv

Saída:

data_candidate/decision_audit_v2_5/human_decisions_validated_v2_5.csv

## 4. Gerar template de follow-up

    python scripts/create_follow_up_template_v2_5.py

Somente decisões com follow_up_required=true são incluídas.

## 5. Registrar eventos de follow-up

Preencher event_at, reviewer_role, follow_up_event_status, follow_up_note e evidence_refs.

## 6. Validar follow-up e estado temporal

    python scripts/validate_follow_up_v2_5.py --events CAMINHO_SEGURO/follow_up_events.csv --as-of 2026-09-27T12:00:00-04:00

Saídas:

- follow_up_events_validated_v2_5.csv;
- follow_up_status_v2_5.csv.

## 7. Revisão visual

    streamlit run app_review_streamlit.py

Usar a aba Auditoria humana v2.5.

## Agentes no Cursor

Executar:

1. DATA-QA;
2. EPIDEMIOLOGIA;
3. OPERACIONAL;
4. PRIVACIDADE;
5. DOCUMENTACAO.

## Regras obrigatórias

- decisão humana não é prova de execução;
- follow-up vencido não é risco;
- nenhuma ação automática;
- nenhuma decisão em nível de paciente;
- nenhuma prescrição;
- nenhum dado pessoal de paciente;
- qualquer escalonamento institucional real permanece fora da automação do repositório.

## Critério de saída

Após acumular decisões reais:

- medir proporção de filas aceitas/encerradas;
- medir decisões que exigem follow-up;
- medir follow-ups abertos/vencidos/concluídos;
- comparar decisão humana com estabilidade v2.4;
- revisar regras com alta discordância;
- manter decisão humana como autoridade final do workflow.
