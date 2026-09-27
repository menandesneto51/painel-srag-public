# Matriz de Ações Sugeridas — SRAG MT v2.2

## Finalidade

Traduzir achados da inteligência territorial em **itens estruturados para revisão humana**.

A matriz não:

- executa ações;
- envia alertas automaticamente;
- prescreve conduta clínica;
- classifica risco por score único;
- substitui decisão de vigilância, gestão ou assistência.

## Domínios

### Qualidade dos dados

Exemplo: revisar oportunidade, completude e inconsistências antes de interpretar o sinal.

### Vigilância epidemiológica

Exemplos:

- validar excesso/tendência;
- verificar coerência regional;
- investigar silêncio epidemiológico.

### Laboratório

Exemplos:

- revisar codificação do agente;
- revisar resultado detectável sem agente informado;
- avaliar cobertura de resultado molecular.

### Rede de Atenção à Saúde

Somente quando existir dimensão assistencial institucional e seu status estiver validado ou em revisão.

### Prevenção e imunização

A matriz apenas orienta revisar as medidas vigentes aplicáveis ao agente/contexto. Não cria esquema vacinal próprio.

### Comunicação de risco

Só é sugerida quando houver sinal epidemiológico relevante e confiança suficiente, e sempre **após validação epidemiológica**.

## Governança

Todo registro gerado contém:

- `suggestion_status = suggested_for_human_review`;
- `human_review_required = true`;
- `automatic_execution = false`;
- `clinical_prescription = false`;
- `composite_score_used = false`.

## Execução no Cursor

```bash
python scripts/build_operational_actions.py
```

Saídas:

- `data_candidate/operational_actions/operational_action_suggestions_v2_2.csv`;
- `data_candidate/operational_actions/operational_action_summary_v2_2.csv`;
- metadata da execução.

## Fontes

A matriz referencia documentos oficiais do Ministério da Saúde em `config/operational_action_matrix_v2_2.json`.

A presença de uma referência não significa que a ação foi automaticamente indicada pelo Ministério para aquele município; significa que a sugestão local deve ser revisada à luz das orientações oficiais vigentes.
