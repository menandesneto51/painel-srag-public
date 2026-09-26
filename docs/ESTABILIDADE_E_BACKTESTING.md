# Estabilidade temporal e backtesting

## Dois conceitos diferentes

### 1. Estimativa por atraso

Pode ser calculada com um único snapshot do SIVEP-Gripe.

Para contagem de casos, a v2 estima:

```text
atraso_caso = DT_DIGITA - DT_SIN_PRI
```

Para desfechos:

```text
atraso_desfecho = DT_ENCERRA - DT_SIN_PRI
```

O lag provisório é o teto, em semanas, de um quantil configurável da distribuição de atrasos (padrão inicial: P95).

Essa abordagem responde:

> Quanto tempo normalmente leva para o evento aparecer/encerrar no sistema?

Ela **não** responde diretamente quanto uma SE continua sendo revisada no banco vivo.

### 2. Backtesting por vintages

Exige múltiplas versões do banco ou dos agregados semanais, capturadas em datas diferentes.

A pergunta é:

> Quando uma SE tinha 1, 2, 3... semanas de idade, quanto seu valor ainda mudou até um snapshot posterior?

Esse é o método preferido para calibrar `stable_week`.

## Lags separados

A v2 não deve usar necessariamente uma única SE estável para tudo.

Pode haver:

- `stable_week_cases`;
- `stable_week_outcomes`;
- `stable_week_virology`.

Óbito/encerramento tende a exigir janela diferente de notificação de caso.

## Regra atual

A regra antiga fixa de duas semanas permanece apenas como provisória/legada.

A promoção para `validated` exige evidência de atraso e, quando vintages suficientes existirem, backtesting de revisão.

## Critério futuro de backtesting

Um critério candidato é considerar uma idade semanal estável quando o percentil 90 da revisão relativa entre vintage e referência posterior for <= 5%, com número mínimo de observações e estabilidade em múltiplos vintages.

O limite definitivo deve ser calibrado e documentado, não assumido.
