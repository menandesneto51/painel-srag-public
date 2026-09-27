# Execução v2.4 no Cursor — Estabilidade Operacional

## Objetivo

Analisar vários vintages da fila v2.2 para separar padrões persistentes de mudanças transitórias do workflow.

A v2.4 não mede risco clínico nem gravidade.

## Pré-requisito

Acumular vintages via v2.3:

```bash
python scripts/run_v2_2_pipeline.py
python scripts/capture_operational_vintage.py
```

Repetir esse processo a cada atualização validada.

## Quantidade mínima útil

O módulo aceita a partir de 2 vintages, mas a configuração inicial foi desenhada para analisar até os **4 vintages mais recentes**.

Parâmetros padrão:

- `window_vintages = 4`;
- persistência mínima = 2 ciclos;
- sustentação = 3 ciclos.

Esses parâmetros são experimentais.

## Executar estabilidade

```bash
python scripts/analyze_operational_stability.py
```

Saídas:

- `data_candidate/operational_stability/operational_stability_v2_4.csv`;
- `operational_stability_summary_v2_4.csv`;
- `operational_stability_report_v2_4.md`.

## Padrões

- `insufficient_history`;
- `routine_stable`;
- `newly_entered_review`;
- `single_cycle_reversion`;
- `persistent_same_queue`;
- `persistent_nonroutine_changed_queue`;
- `recently_returned_to_routine`;
- `oscillating_workflow`;
- `mixed_workflow_history`.

## Métricas de workflow

- nonroutine_cycles;
- nonroutine_fraction;
- current_nonroutine_run;
- longest_nonroutine_run;
- current_same_queue_run;
- queue_change_count;
- workflow_churn_rate;
- single_cycle_reversion_count.

## Revisão visual

```bash
streamlit run app_review_streamlit.py
```

Usar a aba **Estabilidade v2.4**.

## Proteções

Exigir sempre:

- `workflow_stability_is_not_risk = true`;
- `persistence_is_not_severity = true`;
- `transience_is_not_reassurance = true`;
- `automatic_action_enabled = false`;
- `human_review_required = true`.

## Interpretação

### persistent_same_queue

O município permaneceu na mesma fila por múltiplos ciclos.

Isso indica continuidade do **workflow**, não maior gravidade.

### single_cycle_reversion

O município saiu da rotina por um único ciclo e retornou.

Isso não prova que o sinal anterior foi falso.

### oscillating_workflow

A fila mudou repetidamente.

Revisar:

- qualidade dos dados;
- sensibilidade das regras;
- efeito de atraso;
- tags conflitantes;
- possíveis limites muito instáveis.

## Agentes no Cursor

Executar:

1. DATA-QA;
2. EPIDEMIOLOGIA;
3. TERRITORIAL;
4. ESTATISTICA;
5. OPERACIONAL;
6. PRIVACIDADE;
7. DOCUMENTACAO.

## Critério de saída

Após acumular pelo menos 4 vintages:

- revisar padrões de persistência;
- quantificar reversões de um ciclo;
- quantificar churn por fila;
- identificar filas excessivamente instáveis;
- comparar estabilidade com decisões humanas registradas;
- propor, somente depois dessa análise, se alguma regra deve exigir 2 ou mais ciclos antes de determinada revisão de workflow.

Nenhuma regra de persistência entra em produção automaticamente.
