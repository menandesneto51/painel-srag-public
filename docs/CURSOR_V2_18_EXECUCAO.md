# Cursor — execução v2.18

## Fluxo

~~~bash
python scripts/create_learning_cycle_closure_template_v2_18.py
~~~

Preencher revisão humana e decisão.

~~~bash
python scripts/validate_learning_cycle_closure_v2_18.py \
  --input data_candidate/learning_cycle_closure_v2_18/learning_cycle_closure_template_v2_18.csv
python scripts/build_learning_cycle_closure_report_v2_18.py
streamlit run app_review_streamlit.py
~~~

## Gate

`close_learning_cycle` somente quando as ações v2.17 estiverem terminais, cobertura/evidência passarem e, para rule_review, houver handoff revisado.

O AGENTE-GATE-DE-ENCERRAMENTO-DO-APRENDIZADO pode apontar bloqueios e inconsistências, mas não pode fechar o ciclo em nome do humano.
