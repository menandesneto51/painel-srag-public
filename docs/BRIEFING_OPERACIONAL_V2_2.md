# Briefing Estadual Operacional — SRAG MT v2.2

## Objetivo

Agrupar as ações sugeridas em **filas de revisão por domínio, responsável e janela sugerida**.

O briefing deliberadamente não ordena municípios por score ou ranking.

## Estrutura

As filas podem agrupar, por exemplo:

- vigilância epidemiológica;
- qualidade dos dados;
- vigilância laboratorial;
- gestão assistencial/regulação;
- imunização/prevenção;
- CIEVS/comunicação de risco.

## Execução

Depois de gerar a matriz de ações:

```bash
python scripts/build_state_operational_brief.py
```

Saídas:

- `operational_review_queues_v2_2.csv`;
- `state_operational_brief_v2_2.md`;
- metadata.

## Governança

O briefing:

- não é alerta automático;
- não é ordem de serviço;
- não é prescrição clínica;
- não executa ação;
- não usa score composto;
- precisa de revisão humana antes de qualquer encaminhamento.
