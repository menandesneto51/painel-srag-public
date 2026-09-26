# Qualidade e Oportunidade da Vigilância SRAG

## Princípio

Este módulo mede a qualidade operacional do fluxo de informação no SIVEP-Gripe. Ele é deliberadamente separado do risco epidemiológico.

Um município com atraso de digitação ou baixa completude não deve receber automaticamente um "risco alto". Em vez disso, a baixa qualidade reduz a confiança da interpretação e pode gerar ação de qualificação da vigilância.

## Campos utilizados

- `DT_SIN_PRI`: data dos primeiros sintomas;
- `DT_NOTIFIC`: data de preenchimento da ficha;
- `DT_DIGITA`: data de inclusão do registro no sistema;
- `EVOLUCAO`: evolução do caso;
- `CLASSI_FIN`: classificação final;
- `DT_ENCERRA`: data de encerramento.

## Indicadores

### Atraso de notificação

```text
DT_NOTIFIC - DT_SIN_PRI
```

Resumo municipal inicial: mediana em dias, excluindo diferenças negativas do cálculo e contabilizando-as como inconsistência temporal.

### Atraso de digitação

```text
DT_DIGITA - DT_NOTIFIC
```

A data de digitação é a data de inclusão no sistema; alterações posteriores não modificam esse campo segundo o dicionário SIVEP.

### Completude do desfecho

Percentual dos registros com `EVOLUCAO` em:

- 1 — cura;
- 2 — óbito;
- 3 — óbito por outras causas.

`9 — ignorado` não conta como desfecho completo.

### Completude de encerramento

Entre registros com classificação final preenchida e não ignorada, percentual com `DT_ENCERRA` preenchida.

### Inconsistência temporal

Registro com uma ou mais situações:

- notificação anterior ao início dos sintomas;
- digitação anterior à notificação;
- encerramento anterior à notificação.

## Uso operacional

O módulo deve apoiar:

- identificação de municípios com atraso sistemático;
- qualificação de dados;
- priorização de apoio técnico;
- interpretação da confiança dos sinais;
- auditoria de atualização do banco vivo.

## Não uso

Não usar estes indicadores como peso automático de score epidemiológico.

## Próxima etapa

Após o primeiro reprocessamento real:

1. estudar distribuição estadual e regional dos atrasos;
2. definir metas operacionais institucionalmente;
3. testar indicadores por SE estabilizada;
4. criar `confidence_score` transparente;
5. integrar alertas de qualidade ao agente DATA-QA.
