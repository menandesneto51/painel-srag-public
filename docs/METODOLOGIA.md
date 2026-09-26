# Metodologia — Painel SRAG Público v2

## 1. Escopo

O painel monitora SRAG com foco territorial em Mato Grosso a partir de produtos agregados derivados do SIVEP-Gripe e de denominadores populacionais oficiais.

A base pública do Ministério da Saúde é dinâmica ("banco vivo") e sujeita a revisões. Consequentemente, todo produto publicado deve registrar a data da extração e permitir reprodução do recorte.

## 2. Unidade temporal

A unidade principal é a Semana Epidemiológica (SE).

O pipeline deve persistir:

- ano epidemiológico;
- SE do evento/notificação utilizada em cada indicador;
- data inicial da SE;
- data da extração;
- última SE observada;
- última SE considerada estável.

### Semana estável

A SE estável **não pode ser inferida apenas pelo número máximo de SE do calendário**. Deve ser calculada por regra explícita, considerando atraso de notificação/encerramento e o objetivo do indicador.

O metadata nunca pode declarar `stable_week` superior à maior SE observada no conjunto de dados correspondente.

## 3. Denominadores populacionais

Indicadores por 100 mil habitantes devem utilizar estimativa populacional oficial do IBGE correspondente ao ano de referência, salvo justificativa metodológica documentada.

Fórmula padrão:

```text
incidencia_100k = numerador / populacao * 100000
```

O artefato territorial público deve conter, no mínimo:

- código IBGE do município;
- município;
- numerador;
- população utilizada;
- ano da população;
- fonte da população;
- taxa calculada.

Não publicar score territorial derivado de incidência se o denominador não puder ser auditado.

## 4. Indicadores descritivos

### Hospitalização, UTI e óbito

As definições devem ser vinculadas às categorias/códigos do dicionário SIVEP-Gripe vigente na data da extração.

### Letalidade hospitalar

```text
letalidade_hosp_percent = obitos / hospitalizados * 100
```

Deve ser apresentada com denominador explícito e atenção a registros ainda sem evolução encerrada.

### Taxa de UTI entre hospitalizados

```text
taxa_uti_hosp_percent = uti / hospitalizados * 100
```

## 5. Virologia

A distribuição de agentes deve separar, quando possível:

- Influenza A;
- Influenza B;
- SARS-CoV-2;
- VSR;
- rinovírus;
- adenovírus;
- metapneumovírus;
- outros vírus respiratórios;
- agente não identificado/resultado não conclusivo.

A interpretação deve considerar oportunidade de coleta, percentual de casos com resultado laboratorial e possíveis diferenças de testagem.

## 6. Silêncio epidemiológico

"Silêncio" não é sinônimo automático de ausência de doença.

A classificação deverá combinar, de forma documentada:

- histórico esperado do município;
- ausência/redução anômala de notificações;
- oportunidade de notificação;
- capacidade/atividade assistencial, quando disponível;
- contexto regional;
- sinais externos coerentes.

O painel deve distinguir:

- ausência esperada de casos;
- silêncio sob investigação;
- silêncio prioritário;
- problema de qualidade/atraso de dados.

## 7. Risco territorial

O score não deve ser uma soma opaca.

Cada versão deve documentar:

- variáveis componentes;
- transformação/normalização;
- pesos;
- limites das classes;
- tratamento de missing;
- denominadores;
- regra para municípios de pequena população;
- validação retrospectiva.

Enquanto esses itens não estiverem reproduzíveis, o score deve ser rotulado como **experimental/não validado**.

## 8. Odds Ratio

Toda tabela de OR deverá informar:

- população analisada;
- período;
- desfecho;
- grupo de referência;
- número de expostos;
- OR;
- IC95%;
- método de estimação;
- tratamento de missing;
- se a estimativa é bruta ou ajustada.

OR não deve ser descrito como relação causal.

## 9. Nowcasting e forecasting

Previsões devem incluir:

- data de geração;
- período de treinamento;
- método;
- horizonte;
- estimativa pontual;
- intervalo de incerteza;
- backtesting/erro histórico;
- aviso de que projeções não equivalem a casos observados.

## 10. Governança da camada pública

A aplicação pública recebe apenas artefatos aprovados pelo gate de publicação. A camada de produção pode usar dados mais granulares em ambiente institucional controlado, mas esses dados não são transferidos automaticamente para o repositório público.
