# Execução v2.7 no Cursor — Propostas de Mudança de Regra

## Objetivo

Transformar registros v2.6 marcados para revisão de regra em propostas estruturadas, sem alterar automaticamente a matriz vigente.

## Pré-requisito

Executar a v2.6:

    python scripts/build_human_workflow_concordance_v2_6.py

## Gerar propostas

    python scripts/build_rule_change_proposals_v2_7.py

Saídas:

- data_candidate/rule_change_proposals_v2_7/rule_change_proposals_v2_7.csv
- rule_change_proposals_summary_v2_7.json
- rule_change_proposals_report_v2_7.md

## Estados possíveis

- draft
- needs_case_review
- needs_backtest
- needs_epi_review
- needs_statistical_review
- ready_for_human_decision
- approved
- rejected

## Tipos de proposta

- queue_rule
- action_trigger
- threshold
- documentation
- context_requirement

## Regra central

Proposta não é mudança aplicada.

Todo registro deve manter:

- proposal_is_not_change=true
- human_approval_required=true
- automatic_rule_change_enabled=false
- automatic_threshold_change_enabled=false

## Revisão obrigatória

Antes de qualquer aprovação:

1. revisar os casos que originaram a proposta
2. revisar coerência epidemiológica
3. executar backtesting quando houver mudança de lógica/threshold
4. executar revisão estatística quando aplicável
5. atualizar documentação
6. registrar aprovação ou rejeição humana

## App local

    streamlit run app_review_streamlit.py

Usar a aba Propostas de regras v2.7.

## Agentes no Cursor

Executar:

1. AGENTE-CONTROLE-DE-MUDANCAS
2. DATA-QA
3. EPIDEMIOLOGIA
4. ESTATISTICA
5. PRIVACIDADE
6. DOCUMENTACAO

## Proibições

- não editar config operacional automaticamente
- não mudar threshold automaticamente
- não escolher proposta vencedora por score
- não ranquear municípios
- não pontuar revisores
- não promover proposta aprovada diretamente para produção

Uma mudança aprovada deve ser implementada em branch separada, comparada retrospectivamente e passar pelo CI antes de qualquer adoção.


## Modo sombra

A regra candidata deve ser gerada separadamente no Cursor, sem substituir a regra vigente.

Executar:

```bash
python scripts/evaluate_rule_change_shadow_v2_7.py \
  --proposal-id PROP_ID \
  --candidate-queue CAMINHO/fila_candidata.csv \
  --candidate-rule-version candidate-001
```

Saídas por proposta:

- rule_shadow_evaluation_v2_7.csv
- rule_shadow_evaluation_summary_v2_7.json
- rule_shadow_evaluation_report_v2_7.md

O modo sombra compara:

- fila atual;
- fila candidata;
- decisões humanas v2.5, quando disponíveis.

Ele mede mudança de concordância do workflow, não acurácia epidemiológica.

### Leitura correta

- workflow_agreement_improved = maior concordância com decisões humanas registradas;
- workflow_agreement_worsened = menor concordância com o workflow humano;
- nenhuma dessas classes prova desempenho epidemiológico superior/inferior.

### Gate depois do shadow

Mesmo com resultado favorável:

1. proposta continua sem ativação;
2. revisar casos alterados;
3. executar backtesting pertinente;
4. revisar epidemiologia/estatística;
5. atualizar documentação;
6. registrar decisão humana;
7. implementar apenas em branch separada;
8. passar pelo CI antes de adoção.

## Divisão de agentes

### AGENTE-GOVERNANCA-DE-REGRAS

- identifica discordâncias;
- gera contexto para proposta;
- executa/analisa shadow;
- aponta regras/gatilhos para revisão.

### AGENTE-CONTROLE-DE-MUDANCAS

- gerencia status da proposta;
- exige evidências/revisões;
- coordena backtesting;
- registra aprovação/rejeição;
- impede promoção automática.

Os dois agentes não pontuam revisores, não ranqueiam municípios e não ativam regras automaticamente.
