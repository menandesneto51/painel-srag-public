# Confiança do Sinal e Silêncio Epidemiológico — v2

## Separação conceitual

A v2 mantém três dimensões distintas:

1. **atividade epidemiológica** — o que os dados observados indicam;
2. **confiança do sinal** — quão confiáveis/completos/oportunos são os dados usados;
3. **silêncio epidemiológico** — ausência observada em contexto no qual o histórico sugeriria atividade.

Qualidade ruim nunca aumenta automaticamente o risco epidemiológico.

## Confiança do sinal

A classe é rule-based e experimental, sem score numérico.

Componentes iniciais:

- baseline histórico disponível;
- tendência calculável com semanas explícitas;
- qualidade observada;
- atraso mediano sintoma → notificação;
- completude de desfecho;
- inconsistências temporais.

Classes:

- high_experimental;
- moderate_experimental;
- low_experimental;
- insufficient.

Os limiares estão em `config/signal_confidence_v2.json` e exigem backtesting.

## Silêncio

O sinal de silêncio utiliza uma janela de semanas estáveis e requer:

- zero atividade observada na janela;
- baseline histórico válido;
- frequência histórica de semanas com atividade acima do limiar configurado;
- confiança do sinal suficiente.

Saídas possíveis incluem:

- activity_present;
- expected_sparse_or_zero;
- silence_signal_under_review;
- zero_observed_low_confidence;
- zero_observed_context_uncertain;
- insufficient.

Mesmo `silence_signal_under_review` carrega:

`validated_for_operational_alert = false`

até calibração retrospectiva e validação epidemiológica.

## Próxima validação

Avaliar retrospectivamente:

- quantos silêncios correspondem a atraso/subnotificação;
- quantos refletem ausência real de casos;
- impacto de porte populacional;
- efeito do atraso de notificação;
- desempenho por região de saúde;
- duração ótima da janela;
- frequência histórica mínima adequada.
