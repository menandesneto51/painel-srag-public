# v2.5 — Decisão Humana e Follow-up Auditável

## Objetivo

Fechar o ciclo iniciado nas versões anteriores:

`sinal -> revisão -> fila -> sugestão -> decisão humana -> follow-up -> auditoria`

A v2.5 registra decisões. Ela não executa decisões.

## Vínculo de origem

Cada decisão deve estar vinculada a:

- município;
- `snapshot_id`;
- fila de revisão de origem;
- escopo da decisão: fila ou ação;
- `action_id`, quando a decisão se refere a uma sugestão específica;
- data/hora;
- papel do revisor;
- decisão;
- justificativa;
- evidências consultadas.

O sistema rejeita decisão cuja fila não corresponda à fila municipal de origem ou cujo `action_id` não exista nas sugestões do município.

## Identidade do revisor

A camada pública/técnica armazena apenas:

`reviewer_role`

Não armazenar nome, CPF, matrícula, e-mail ou outro identificador pessoal neste artefato.

Se a instituição exigir assinatura nominal, isso deve ficar em sistema/documento institucional apropriado, separado do dataset candidato.

## Follow-up

Quando `follow_up_required=true`, são obrigatórios:

- prazo posterior à decisão;
- papel responsável pelo follow-up.

Eventos permitidos:

- acknowledged;
- in_progress;
- completed;
- cancelled.

O estado derivado pode ser:

- not_required;
- open;
- overdue;
- completed;
- cancelled.

`overdue` não é classe de risco epidemiológico.

## Regra central

`decision_is_not_proof_of_execution = true`

Uma decisão do tipo `request_epi_investigation`, por exemplo, registra a decisão de solicitar investigação. Não prova que a investigação foi realizada.

Da mesma forma, um evento de follow-up é um registro humano do acompanhamento, não uma integração automática com sistemas externos.

## Execução no Cursor

### 1. Gerar template contextualizado

```bash
python scripts/create_decision_audit_template_v2_5.py
```

### 2. Preencher somente as linhas realmente revisadas

O template pode conter os 142 municípios, mas o arquivo submetido à validação deve conter apenas decisões efetivamente tomadas.

### 3. Validar decisões

```bash
python scripts/validate_decision_audit_v2_5.py \
  --input CAMINHO/decisoes_preenchidas.csv
```

### 4. Gerar template de follow-up

```bash
python scripts/create_follow_up_template_v2_5.py
```

### 5. Validar eventos e gerar estado temporal

```bash
python scripts/validate_follow_up_v2_5.py \
  --events CAMINHO/follow_up_preenchido.csv \
  --as-of 2026-09-30T12:00:00-04:00
```

O parâmetro `--as-of` é obrigatório para que `overdue` seja reprodutível.

### 6. Gerar auditoria estadual

```bash
python scripts/build_decision_audit_report_v2_5.py
```

## Proteções

Sempre:

- decisão humana = true;
- execução automática = false;
- decisão em nível de paciente = false;
- prescrição clínica = false;
- decisão ≠ prova de execução;
- follow-up ≠ risco;
- identificador pessoal do revisor = não armazenado;
- promoção pública = bloqueada.
