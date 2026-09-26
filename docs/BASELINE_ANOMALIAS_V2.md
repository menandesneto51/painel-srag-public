# Baseline, Tendência e Anomalias — SRAG MT v2

## Status

**Experimental / under_calibration.**

Este módulo produz sinais analíticos, não alertas operacionais validados.

## Objetivo

Separar três perguntas:

1. **Nível:** o observado está acima do padrão sazonal histórico?
2. **Tendência:** as semanas estáveis mais recentes estão crescendo ou diminuindo?
3. **Concordância:** excesso histórico e tendência apontam na mesma direção?

Nenhum desses sinais substitui revisão epidemiológica.

## Histórico esperado

Entrada mínima por município e SE:

- ANO;
- SE;
- código IBGE;
- município;
- população;
- casos;
- hospitalizações;
- UTI;
- óbitos.

Semanas com zero devem existir explicitamente. Ausência de linha não é tratada automaticamente como zero.

## Baseline sazonal

Padrão inicial:

- anos históricos anteriores ao ano-alvo;
- janela sazonal de ±2 SE;
- centro = mediana;
- dispersão = MAD;
- Q25 e Q75 preservados;
- mínimo de 3 anos históricos.

O uso de MAD reduz sensibilidade a anos epidêmicos extremos, mas ainda exige backtesting local.

## Anomalia

Para MAD > 0:

`robust_z = (observado - mediana) / (1.4826 * MAD)`

Limiar inicial configurado: 3,5.

Esse limiar é **experimental** e deverá ser recalibrado em Mato Grosso.

Quando MAD = 0, o sistema não fabrica z-score; produz apenas uma classificação descritiva experimental baseada no desvio determinístico em relação ao histórico.

## Tendência

Comparação inicial:

- média das 2 últimas SE estáveis;
- média das 2 SE estáveis anteriores;
- pseudocontagem = 0,5.

Saídas:

- razão;
- log2 da razão;
- status de completude.

A pseudocontagem evita divisão por zero, mas não converte pequeno número em evidência forte.

## Sinal combinado

Categorias experimentais:

- elevated_and_rising_experimental;
- elevated_not_rising_experimental;
- rising_without_baseline_excess_experimental;
- no_combined_signal_experimental.

Todos carregam:

`validated_for_operational_alert = false`

até conclusão de backtesting, análise de sensibilidade e revisão epidemiológica/estatística.

## Próximo passo metodológico

O backtesting deverá medir, por município e agregado estadual/regional:

- sensibilidade;
- especificidade;
- PPV;
- estabilidade semana a semana;
- frequência de falsos sinais em pequenos municípios;
- antecedência em relação a picos reconhecidos;
- concordância com pressão assistencial e virologia;
- impacto da regra de semana estável.

Depois do backtesting, os limiares poderão ser mantidos, alterados ou abandonados.
