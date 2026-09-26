# Silêncio Epidemiológico v2 — P2

## Princípio central

**Zero notificação não é sinônimo automático de silêncio epidemiológico.**

A OMS diferencia um **zero reportado** de uma ausência de submissão: zero em um sistema que estava operando carrega informação; ausência de dados pode significar falha de vigilância/notificação.

Referência:
https://www.who.int/publications/journals/weekly-epidemiological-record/wer101-38

## Limitação do SIVEP

O SIVEP-Gripe não fornece, neste projeto, um mecanismo municipal explícito de "zero reportado".

Portanto a v2 distingue:

- `explicit_zero_report` — somente se houver fonte institucional específica;
- `recent_reporting_activity` — proxy baseado em atividade prévia de notificação;
- `none`;
- `unknown`.

**Recent reporting activity é proxy, não prova de zero-reporting formal.**

## Classes experimentais

### not_silent

Há casos observados.

### absence_compatible_with_expected

Zero observado e histórico também compatível com zero/atividade mínima.

### silence_under_investigation

Zero observado apesar de histórico com atividade esperada. Exige verificação.

### silence_priority_candidate

Além da condição anterior:

- expectativa histórica mínima configurada;
- evidência de funcionamento recente da notificação;
- qualidade não baixa/insuficiente;
- sinal regional persistente configurado.

Ainda é **candidato**, não conclusão automática.

### data_quality_or_reporting_gap

Histórico sugere atividade, mas faltam evidências suficientes de qualidade/funcionamento da notificação.

### insufficient_baseline

Não há histórico suficiente para interpretar o zero.

## Separação de risco

O silêncio não é convertido diretamente em score de risco. Ele gera uma tarefa de verificação epidemiológica/qualidade.

## Próxima integração

Para operacionalização municipal serão necessários:

- baseline municipal histórico por contagem;
- harmonização de municípios/códigos;
- evidência de atividade de notificação em janela anterior;
- qualidade municipal;
- sinal regional;
- eventualmente dados assistenciais institucionais.
