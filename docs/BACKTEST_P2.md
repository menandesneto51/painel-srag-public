# Backtesting P2 — Anomalias SRAG MT

## Finalidade

Calibrar limiares analíticos sem tratá-los como verdade clínica.

O backtesting utiliza anos históricos em ordem temporal. Para cada ano holdout:

1. somente anos anteriores entram no treinamento;
2. o baseline sazonal é recalculado;
3. o ano holdout é tratado como se fosse corrente;
4. robust-z é calculado;
5. o sinal é comparado a uma definição interna de alta atividade futura.

## Alvo de calibração

O alvo inicial é:

`máximo observado nas N semanas subsequentes completas >= quantil histórico municipal`

Configuração inicial:

- métrica: hospitalizações;
- janela futura: 2 semanas;
- quantil: 0,90;
- limiares robust-z: 2,5; 3,0; 3,5; 4,0.

Esse alvo é **interno**. Não é padrão-ouro epidemiológico e não valida automaticamente alerta operacional.

## Métricas

- sensibilidade;
- especificidade;
- PPV;
- NPV;
- taxa de sinal;
- taxa de evento.

Também são preservadas as predições linha a linha para auditoria.

## Regras

- não usar dados futuros no treinamento;
- não escolher limiar somente pelo maior desempenho agregado;
- estratificar resultados por porte municipal;
- avaliar anos pandêmicos separadamente;
- revisar falsos positivos e falsos negativos;
- comparar posteriormente com virologia e pressão assistencial.

## Promoção

Nenhum resultado deste módulo altera:

- `publication_status`;
- score de risco;
- classe territorial;
- alerta operacional.

O status permanece:

`experimental_internal_calibration`
