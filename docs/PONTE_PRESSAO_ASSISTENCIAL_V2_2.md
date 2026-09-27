# Ponte Sanitizada de Pressão Assistencial — v2.2

## Objetivo

Permitir que a inteligência territorial receba **somente agregados municipais previamente validados**, sem transportar dados individuais para o repositório público.

## Contrato mínimo

- codigo_ibge;
- reference_week;
- pressure_status;
- validation_status;
- source_scope.

Campos agregados opcionais:

- hospital_occupancy_percent;
- icu_occupancy_percent;
- open_requests;
- pending_transfers;
- waiting_admission;
- source_updated_at;
- pressure_evidence.

## Proteções

A ponte rejeita:

- CPF;
- CNS;
- nome de paciente;
- nascimento;
- telefone;
- endereço;
- prontuário;
- e-mail;
- identificadores/documentos;
- campos fora do contrato agregado.

Ela também não calcula automaticamente `pressure_status`.

O status precisa vir de uma fonte institucional agregada e validada externamente.

## Cursor

Exemplo:

```bash
python scripts/sanitize_healthcare_pressure.py \
  --input CAMINHO_SEGURO/pressao_assistencial_agregada.csv \
  --stable-week 39
```

Saída:

`data_candidate/healthcare_pressure_sanitized.csv`

Esse artefato pode então ser passado a:

```bash
python scripts/build_territorial_intelligence.py \
  --healthcare-pressure data_candidate/healthcare_pressure_sanitized.csv
```
