# Cursor — execução v2.17

## Pré-condição

Executar sobre `postmortem_validated_v2_14.csv` validado.

## Fluxo

~~~bash
python scripts/create_learning_action_followup_template_v2_17.py
~~~

Preencher o template no ambiente local/institucional, usando apenas slugs técnicos de papel (ex.: `epidemiologia`, `revisao_epidemiologica`) para responsável/verificador. Não inserir nomes, CPF, CNS, e-mail, telefone ou outros identificadores em campos textuais/evidências.

Validar com instante explícito:

~~~bash
python scripts/validate_learning_action_followup_v2_17.py \
  --input data_candidate/learning_action_followup_v2_17/learning_action_followup_template_v2_17.csv \
  --as-of 2026-10-31T12:00:00-04:00
~~~

Gerar relatório:

~~~bash
python scripts/build_learning_action_followup_report_v2_17.py
~~~

Revisar no app local:

~~~bash
streamlit run app_review_streamlit.py
~~~

## Gate

- conclusão exige `completed_at` e evidência;
- verificação `verified/rejected` exige horário, papel e notas;
- `rule_review` concluída exige `governance_handoff_ref`;
- atraso não é risco;
- conclusão não é prova de efetividade;
- verificação humana não é inferência de efeito epidemiológico;
- nenhuma issue, regra, deploy, rollback ou ação é executada automaticamente.

## Agente

Executar `AGENTE-FOLLOWUP-DE-APRENDIZADO` como apoio à checagem de prazos, evidências, bloqueios e handoffs. O agente não pode fechar ação, verificar evidência ou criar handoff em nome do humano.
