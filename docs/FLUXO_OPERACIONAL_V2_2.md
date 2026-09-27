# Fluxo Operacional Unificado SRAG MT v2.2

## Camadas complementares

A v2.2 mantém dois produtos diferentes, deliberadamente:

### 1. Fila municipal de revisão

Cobertura obrigatória dos 142 municípios.

Responde:

> Qual fluxo de revisão técnica deve receber este município?

Ela **não** é ranking de risco.

### 2. Sugestões de ações

Geradas apenas quando os gatilhos documentados são atendidos.

Respondem:

> Quais itens devem ser considerados pelos revisores humanos à luz das evidências e das orientações oficiais?

Elas **não** são ordens nem execução automática.

## Orquestrador

No Cursor:

```bash
python scripts/run_v2_2_pipeline.py
```

Pré-requisitos:

```bash
python scripts/build_territorial_intelligence.py
python scripts/build_territorial_review_cards.py
```

## Saídas

Diretório:

`data_candidate/operational_v2_2/`

Arquivos:

- `municipal_review_queue_v2_2.csv` — 142 municípios;
- `operational_action_suggestions_v2_2.csv`;
- `operational_action_summary_v2_2.csv`;
- `domain_review_queues_v2_2.csv`;
- `state_review_report_v2_2.md`;
- `state_operational_brief_v2_2.md`;
- `state_review_summary_v2_2.json`;
- `v2_2_manifest.json`.

## Travas obrigatórias

- execução automática = false;
- decisão em nível de paciente = false;
- prescrição clínica = false;
- score composto = false;
- fila não é ranking de risco;
- revisão humana = obrigatória;
- promoção pública = bloqueada.

## Interpretação

Um município pode estar em uma fila de revisão mesmo sem receber uma sugestão específica.

Isso é esperado: a fila organiza o trabalho; a matriz de ações só gera itens quando existe um gatilho documentado.
