# Detecção de Anomalias — P2

## Status

**Experimental. Não é classificação de risco.**

O módulo compara o observado até uma semana epidemiológica estável com um baseline sazonal explicitamente selecionado.

## Método inicial

Para cada SE:

1. mediana histórica;
2. MAD como dispersão principal;
3. IQR como fallback quando MAD = 0;
4. desvio robusto padronizado;
5. excesso absoluto e relativo;
6. sinal candidato quando o desvio ultrapassa o limiar configurado.

## Persistência

Um extremo isolado recebe:

`candidate_elevated`

Somente após persistência configurável em semanas consecutivas passa a:

`persistent_elevated`

Isso reduz a chance de transformar um único ponto extremo em alerta operacional.

## Sem dispersão histórica

Quando MAD = 0 e IQR = 0, o módulo não cria z infinito. O status é:

`no_historical_dispersion`

Esse cenário exige revisão epidemiológica.

## Pequena base histórica

Se a SE tiver menos anos que `min_baseline_years`, o status é:

`insufficient_baseline`

## Limiares

Os valores iniciais estão em `config/anomaly_v2.json` e são experimentais. Devem ser calibrados por backtesting e análise de sensibilidade antes de qualquer uso operacional.

## Saída

- observado;
- mediana;
- Q25/Q75;
- MAD;
- número de anos;
- excesso absoluto/relativo;
- desvio robusto;
- método de dispersão;
- persistência;
- status do sinal;
- versão/status do modelo.

Nenhuma coluna produz automaticamente classe Baixo/Moderado/Alto.
