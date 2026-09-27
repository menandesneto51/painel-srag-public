# Execução v2.2 no Cursor — Apoio Operacional Explicável

## Objetivo

Gerar uma fila de revisão municipal e relatório estadual a partir dos artefatos v2.1, sem criar score, ranking de risco ou execução automática.

## Pré-requisitos

Executar antes:

```bash
python scripts/build_virology_metrics.py
python scripts/run_p2_pipeline.py
python scripts/build_territorial_intelligence.py
python scripts/build_territorial_review_cards.py
```

## Pressão assistencial — opcional

Se houver fonte institucional agregada:

```bash
python scripts/sanitize_healthcare_pressure.py \
  --input CAMINHO_SEGURO/pressao_assistencial_agregada.csv \
  --stable-week <SE_ESTAVEL>
```

A ponte rejeita colunas potencialmente identificáveis e campos fora do contrato agregado.

Depois, reconstruir a inteligência territorial:

```bash
python scripts/build_territorial_intelligence.py \
  --healthcare-pressure data_candidate/healthcare_pressure_sanitized.csv
```

## Gerar fila operacional

```bash
python scripts/build_operational_review.py
```

Saídas:

- `data_candidate/operational_review/operational_review_queue_v2_2.csv`;
- `data_candidate/operational_review/state_review_summary_v2_2.json`;
- `data_candidate/operational_review/state_review_report_v2_2.md`.

## Revisão visual

```bash
streamlit run app_review_streamlit.py
```

Usar a aba **Revisão operacional v2.2**.

## Regras obrigatórias

A fila:

- não é ranking de risco;
- não é lista de gravidade;
- não executa ações;
- não toma decisão em nível de paciente;
- não substitui epidemiologista, assistência, regulação ou gestão;
- deve cobrir 142 municípios.

Cada linha precisa manter:

- `human_review_required = true`;
- `automatic_execution_enabled = false`;
- `patient_level_decision_enabled = false`;
- `composite_score_used = false`;
- `queue_is_not_risk_rank = true`.

## Filas iniciais

- `data_validation_first`;
- `targeted_silence_verification`;
- `multidisciplinary_review`;
- `epidemiology_virology_review`;
- `epidemiology_review`;
- `laboratory_review`;
- `routine_monitoring`.

A ordem acima não representa prioridade clínica ou risco.

## Agentes

Executar revisão na ordem:

1. DATA-QA;
2. EPIDEMIOLOGIA;
3. TERRITORIAL;
4. ESTATISTICA;
5. PRIVACIDADE;
6. DOCUMENTACAO.

Se houver pressão assistencial:

7. ASSISTENCIAL/REGULACAO — revisão institucional fora da camada pública.

## Critério de saída

Produzir relatório com:

- distribuição dos 142 municípios por fila;
- justificativas e tags;
- campos desconhecidos/regras não mapeadas;
- achados dos agentes;
- municípios que exigem revisão multidisciplinar;
- limitações;
- decisão humana registrada.

Não promover artefatos v2.2 para `data_public/` nesta etapa.


## Registro da decisão humana

Gerar template municipal:

```bash
python scripts/create_human_review_template.py
```

Após preenchimento manual, validar:

```bash
python scripts/validate_human_review_decisions.py \
  --input CAMINHO_SEGURO/human_review_decisions.csv
```

Decisões permitidas:

- continue_monitoring;
- request_data_validation;
- request_epi_investigation;
- request_laboratory_review;
- request_assistance_coordination;
- request_multidisciplinary_review;
- closed_no_escalation.

O registro é auditável, mas não executa a ação e não altera automaticamente o painel público.
