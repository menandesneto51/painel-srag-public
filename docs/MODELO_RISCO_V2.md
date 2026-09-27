# Modelo de Risco SRAG v2 — especificação experimental

## Status

**EXPERIMENTAL / NÃO VALIDADO PARA PUBLICAÇÃO**

O score legado não será recalculado nem reproduzido por aproximação porque sua fórmula não está documentada no repositório e os denominadores que o alimentaram apresentaram inconsistências relevantes.

A v2 substitui a lógica opaca por dimensões separadas e auditáveis.

## Referências de desenho

- Ministério da Saúde — Guia de Vigilância Integrada da Covid-19, Influenza e Outros Vírus Respiratórios de Importância em Saúde Pública:
  https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/guias-e-manuais/2024/guia-vigilancia-integrada-da-covid-19-influenza-e-outros-virus-respiratorios-de-importancia-em-saude-publica/view
- OpenDataSUS — banco vivo SIVEP-Gripe:
  https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026
- CDC — Hospital Respiratory Data methodology:
  https://www.cdc.gov/nhsn/psc/hospital-respiratory-reporting/data-methods.html

A referência do CDC é usada como benchmark metodológico para classificação histórica de taxas de hospitalização; não como regra transplantada automaticamente para Mato Grosso.

## 1. Princípio

O município não recebe um "risco" apenas por ter:

- pequena população;
- um único caso grave;
- 100% de UTI em denominador muito pequeno;
- atraso/silêncio de notificação.

Qualidade da informação é medida separadamente e gera **confiança**, não aumento artificial do risco.

## 2. Dimensões

### A. Atividade

Indicador-base preferencial:

`taxa_srag_hospitalizada_se_100k = hospitalizacoes_na_SE / populacao * 100000`

A classificação deverá ser calibrada contra histórico de Mato Grosso, preferencialmente considerando sazonalidade e múltiplos anos.

### B. Tendência

Comparar janelas equivalentes e estabilizadas.

Exemplo inicial para backtesting:

`razao_tendencia = media_ultimas_2_SE / media_2_SE_anteriores`

A razão deve usar pseudocontagem ou regra explícita para zeros e não deve ser aplicada às semanas ainda sujeitas a atraso excessivo.

### C. Gravidade

Separar:

- proporção de UTI entre hospitalizados;
- letalidade entre registros elegíveis ao desfecho.

Proporções de pequenos denominadores devem usar suavização/estimativa com incerteza. O painel não deve tratar 1/1 como evidência equivalente a 100/100.

### D. Virologia

Indicadores candidatos:

- positividade entre registros testados;
- composição viral;
- crescimento de Influenza, VSR, SARS-CoV-2 e outros vírus;
- mudança de predominância.

A ausência de teste não deve ser interpretada como ausência de circulação.

### E. Pressão assistencial

Quando dados institucionais estiverem disponíveis:

- internações recentes;
- ocupação;
- demanda por UTI;
- disponibilidade/capacidade;
- regulação/SISREG.

Esta dimensão deve ser mantida fora do repositório público quando a fonte tiver restrição institucional.

## 3. Confiança do sinal

Criar `confidence_score` independente do risco.

Componentes candidatos:

- completude;
- oportunidade;
- volume mínimo;
- estabilidade da SE;
- disponibilidade laboratorial;
- consistência temporal;
- cobertura territorial.

Saída recomendada:

- alta;
- moderada;
- baixa;
- insuficiente.

Um município pode ter **sinal de risco alto com confiança baixa**; a interface deve mostrar as duas coisas.

## 4. Pequenos números

Para proporções de gravidade, a v2 utilizará abordagem de suavização parametrizada e documentada.

Exemplo:

`posterior = (eventos + prior_strength * taxa_estadual) / (denominador + prior_strength)`

O parâmetro `prior_strength` deverá ser definido por calibração/backtesting, não por conveniência visual.

## 5. Classificação de atividade

Antes de definir cortes definitivos:

1. montar histórico semanal municipal/estadual;
2. excluir períodos ou semanas inadequados mediante justificativa;
3. estudar distribuição por temporada;
4. testar agrupamento/percentis;
5. realizar backtesting;
6. avaliar estabilidade em municípios pequenos;
7. comparar com eventos conhecidos e pressão assistencial.

O benchmark do CDC usa agrupamento k-medians e percentis sobre taxas históricas de hospitalização para obter categorias interpretáveis. A v2 poderá testar abordagem semelhante, mas os limites serão calibrados com dados de Mato Grosso.

## 6. Score composto

**Não ativar ainda.**

Enquanto as dimensões não forem calibradas individualmente, a interface deve mostrar um painel multidimensional, não um número único.

Uma futura composição somente será aceita se houver:

- pesos explícitos;
- análise de sensibilidade;
- backtesting;
- comparação contra versão multidimensional;
- justificativa epidemiológica;
- validação documentada.

## 7. Classes operacionais

Até a calibração, usar:

- `experimental`
- `under_calibration`
- `validated`

Não converter automaticamente em Baixo/Moderado/Alto/Muito Alto.

## 8. Regra de promoção

O modelo só poderá ser marcado como `validated` após:

- denominadores auditados;
- histórico reconstruído;
- backtesting;
- revisão epidemiológica;
- revisão estatística;
- revisão dos agentes;
- aprovação humana registrada.
