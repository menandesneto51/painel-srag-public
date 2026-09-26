# Virologia Temporal — SRAG-MT v2

## Objetivo

Reconstruir a circulação temporal dos vírus respiratórios registrados no SIVEP-Gripe sem assumir denominadores laboratoriais que o banco não comprova.

## Campos moleculares

A v2 utiliza:

- `PCR_RESUL`: resultado do RT-PCR/outro método molecular;
- `POS_PCRFLU`: positivo para Influenza;
- `TP_FLU_PCR`: Influenza A/B;
- `POS_PCROUT`: positivo para outros vírus;
- `PCR_SARS2`;
- `PCR_VSR`;
- `PCR_PARA1` a `PCR_PARA4`;
- `PCR_ADENO`;
- `PCR_METAP`;
- `PCR_BOCA`;
- `PCR_RINO`;
- `PCR_OUTRO`.

## Regras

### Resultado molecular interpretável

`PCR_RESUL` em:

- 1 — detectável;
- 2 — não detectável;
- 3 — inconclusivo.

A cobertura de resultado molecular é apresentada como indicador operacional. Para análises de positividade estrita, o denominador deverá ser redefinido conforme a pergunta analítica.

### Detecções

Cada agente marcado é contado como detecção.

Um registro pode conter mais de um agente. Portanto:

- coinfecção é permitida;
- soma das detecções pode superar o número de registros positivos;
- distribuição por vírus não é forçada a ser mutuamente exclusiva.

### Detectável sem agente codificado

Se `PCR_RESUL = 1` mas nenhum agente previsto estiver marcado, a saída registra:

`Detectável sem agente codificado`

Isso evita classificar arbitrariamente o agente.

## O que NÃO calcular automaticamente

A v2 não calcula "positividade específica por vírus" usando todos os testes moleculares como denominador, porque ausência de marcador de um agente não comprova que aquele agente foi efetivamente pesquisado no painel laboratorial utilizado.

## Saídas

- `virology_weekly_mt_2026.csv`;
- `virology_municipal_weekly_mt_2026.csv`;
- `virology_metadata.json`.

## Indicadores

- detecções por vírus e SE;
- participação entre detecções;
- cobertura de resultado molecular;
- número de resultados detectáveis;
- coinfecções;
- detectáveis sem agente codificado.

## Próximos passos

Após o primeiro reprocessamento real:

1. avaliar completude por agente/tempo;
2. comparar com GAL/LACEN quando disponível;
3. investigar mudanças de painel diagnóstico;
4. validar denominadores de positividade por agente;
5. construir baseline sazonal por vírus;
6. alimentar detecção de anomalias sem usar contagens laboratoriais isoladas como causalidade.
