# Execução da Inteligência Territorial v2.1 no Cursor

## Pré-requisitos

Executar antes:

```bash
python scripts/build_virology_metrics.py
python scripts/run_p2_pipeline.py
```

## Execução sem pressão assistencial

```bash
python scripts/build_territorial_intelligence.py
```

Saídas:

- `data_candidate/territorial_intelligence/territorial_intelligence_v2_1.csv`
- `data_candidate/territorial_intelligence/territorial_intelligence_v2_1.metadata.json`

## Execução com pressão assistencial institucional

```bash
python scripts/build_territorial_intelligence.py \
  --healthcare-pressure CAMINHO_SEGURO/healthcare_pressure.csv
```

O arquivo institucional não deve ser copiado para o repositório.

Contrato mínimo documentado em:

`config/healthcare_pressure.schema.json`

## Leitura recomendada

Para cada município interpretar separadamente:

1. `signal_status`;
2. `signal_confidence`;
3. `silence_status`;
4. `virology_status`;
5. `virology_dominant_agent`;
6. `pressure_status`, se disponível e validado.

Não existe score composto.

## Proteções

O artefato sempre nasce com:

- `territorial_model_status = under_calibration`;
- `composite_score = NA`;
- `operational_alert = false`;
- `validated_for_operational_alert = false`.

O arquivo permanece em `data_candidate/` até que exista calibração e revisão humana.
