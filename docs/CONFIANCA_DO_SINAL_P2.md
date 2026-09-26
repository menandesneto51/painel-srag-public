# Confiança do Sinal — P2

## Princípio

Confiança responde:

> Quanto podemos confiar que o sinal observado representa adequadamente o que está acontecendo?

Ela **não** responde:

> Qual é o risco epidemiológico?

As duas dimensões permanecem separadas.

## Sem score numérico oculto

Nesta versão:

`numeric_score_enabled = false`

Cada componente recebe uma classe explícita:

- high;
- moderate;
- low;
- insufficient.

A confiança geral é a **pior classe entre as dimensões essenciais**. Isso é conservador, mas completamente auditável.

## Dimensões essenciais

- estabilidade temporal;
- volume;
- completude do desfecho;
- oportunidade de notificação;
- consistência temporal.

Uma dimensão essencial insuficiente impede confiança alta/moderada.

## Dimensões opcionais

- cobertura laboratorial;
- profundidade de vintages;
- profundidade do baseline histórico.

Elas são exibidas e podem se tornar essenciais após calibração, mas não entram silenciosamente na regra atual.

## Limiares

Os limiares iniciais estão em:

`config/confidence_v2.json`

São **experimentais** e precisam ser calibrados com a operação real da vigilância estadual.

## Uso

O perfil de confiança deve acompanhar:

- anomalias;
- silêncio epidemiológico;
- forecast;
- comparações territoriais.

Exemplo de interpretação:

- sinal elevado + confiança alta → investigação epidemiológica prioritária;
- sinal elevado + confiança baixa → primeiro avaliar atraso/completude/qualidade;
- sinal normal + confiança insuficiente → não concluir ausência de problema.

Essas frases são regras de interpretação, não automatização de decisão.
