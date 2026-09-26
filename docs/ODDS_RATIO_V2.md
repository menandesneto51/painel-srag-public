# Odds Ratio — metodologia v2

## Status

A v2 substitui as tabelas legadas sem método explícito por cálculo reproduzível.

Nesta primeira etapa o painel calcula apenas **Odds Ratio bruta (2×2)**.

## Desfechos

### Óbito por SRAG

- caso: `EVOLUCAO = 2`;
- controle: `EVOLUCAO = 1`;
- óbito por outras causas, ignorado e ausente não entram nessa comparação.

### UTI

- caso: `UTI = 1`;
- controle: `UTI = 2`;
- ignorado/ausente é excluído.

## Exposições

Inicialmente:

- doença hepática;
- doença renal;
- imunodepressão;
- doença neurológica;
- pneumopatia;
- obesidade;
- diabetes;
- asma;
- cardiopatia;
- puerpério;
- sexo masculino;
- gestação;
- idade >= 60 anos.

Missing é excluído de forma pareada para cada exposição/desfecho.

## Tabela 2×2

```text
                    Desfecho +   Desfecho -
Exposto                  a            b
Não exposto              c            d
```

```text
OR = (a*d)/(b*c)
```

IC95% aproximado na escala log:

```text
SE(log OR) = sqrt(1/a + 1/b + 1/c + 1/d)
IC95% = exp(log(OR) ± 1.96*SE)
```

## Células zero

Se qualquer célula for zero, aplica-se correção Haldane–Anscombe de 0,5 a todas as quatro células. A saída registra explicitamente quando a correção foi utilizada.

## Interpretação

- OR é medida de associação, não causalidade;
- OR bruta não controla confundimento;
- IC amplo indica baixa precisão;
- pequeno número de expostos deve ser explicitamente considerado;
- comparações com o legado devem ser metodológicas, não apenas numéricas.

## Ajuste multivariado

Ainda bloqueado.

Uma futura regressão logística ajustada deverá especificar a priori covariáveis, tratamento de idade, interações, missing, colinearidade, tamanho amostral/eventos por parâmetro, validação e calibração.

A tabela ajustada nunca deve substituir a bruta sem identificação clara do modelo.
