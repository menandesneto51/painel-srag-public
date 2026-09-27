# App de Revisão Local — SRAG MT v2.1

Arquivo:

`app_review_streamlit.py`

## Finalidade

Inspecionar os artefatos de `data_candidate/` antes de promoção.

Ele é separado de:

`app_publico_streamlit.py`

e não deve ser publicado como painel oficial.

## Execução no Cursor

Após P1/P2/v2.1:

```bash
streamlit run app_review_streamlit.py
```

## Conteúdo

- inteligência territorial multidimensional;
- atividade/tendência/anomalia;
- confiança do sinal;
- silêncio epidemiológico;
- virologia;
- backtesting.

## Segurança

O app:

- não lê microdados SIVEP;
- não usa bases nominais;
- não altera `publication_status`;
- não promove arquivos;
- não gera score composto;
- não gera alerta operacional.

Seu uso é exclusivamente de revisão técnica/epidemiológica.
