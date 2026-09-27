> **SUPERSEDED:** este fluxo v2.2 é mantido apenas por compatibilidade histórica. O caminho canônico para novas execuções é a v2.5 documentada em `docs/AUDITORIA_DECISAO_HUMANA_V2_5.md` e `docs/CURSOR_V2_5_EXECUCAO.md`.

# Registro de Decisão Humana — v2.2

## Finalidade

Registrar a conclusão da revisão municipal de forma separada da fila automática.

A fila sugere **o tipo de revisão**. Apenas uma pessoa responsável registra **a decisão**.

## Decisões permitidas

- continue_monitoring;
- request_data_validation;
- request_epi_investigation;
- request_laboratory_review;
- request_assistance_coordination;
- request_multidisciplinary_review;
- closed_no_escalation.

Esses estados documentam decisão de workflow; não executam automaticamente a ação.

## Fluxo no Cursor

Gerar template:

```bash
python scripts/create_human_review_template.py
```

Preencher manualmente os campos:

- reviewed_at;
- reviewer_role;
- decision_status;
- rationale;
- evidence_refs;
- notes.

Validar:

```bash
python scripts/validate_human_review_decisions.py \
  --input CAMINHO_SEGURO/human_review_decisions.csv
```

## Proteções

A saída validada contém:

- `decision_recorded_by_human = true`;
- `automatic_execution_enabled = false`;
- `patient_level_decision_enabled = false`.

Nenhum registro de decisão humana altera sozinho o painel público ou `publication_status`.
