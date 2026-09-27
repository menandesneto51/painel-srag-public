# Dicionário de Indicadores — Painel SRAG Público v2

## Convenções

- **Fonte epidemiológica principal:** SIVEP-Gripe.
- **Base territorial:** município de residência.
- **Chave territorial:** código IBGE municipal.
- **Denominador populacional:** estimativa IBGE 2026, referência 01/07/2026.
- **Unidade temporal principal:** Semana Epidemiológica (SE).
- **Status do modelo territorial composto:** em calibração.

## Indicadores descritivos

### casos

Número de registros SRAG elegíveis no recorte adotado.

**Unidade:** contagem.

### hospitalizacoes

Número de registros com `HOSPITAL = 1`.

**Unidade:** contagem.

### uti

Número de registros com `UTI = 1`.

**Unidade:** contagem.

### obitos

Número de registros com `EVOLUCAO = 2` (óbito por SRAG), conforme dicionário operacional utilizado.

**Unidade:** contagem.

### curas

Número de registros com `EVOLUCAO = 1`.

**Unidade:** contagem.

## Indicadores territoriais

### incidencia_srag_100k

```text
casos / população * 100000
```

### hospitalizacao_100k

```text
hospitalizações / população * 100000
```

### uti_100k

```text
UTI / população * 100000
```

### obito_100k

```text
óbitos / população * 100000
```

## Indicadores do snapshot legado

Os campos abaixo são preservados apenas para auditoria histórica enquanto o snapshot antigo estiver em revisão:

- `incidencia_100k_legacy`;
- `incidencia_recente_100k_legacy`;
- `score_risco_srag_legacy`;
- `classe_risco_srag_legacy`.

Eles não devem ser reutilizados como saída do modelo v2.

## Qualidade e confiança

### publication_status

Estados permitidos:

- `blocked`: contém inconsistência conhecida ou ainda não passou por todos os gates;
- `under_review`: em revisão;
- `validated`: aprovado para publicação;
- `superseded`: substituído por snapshot posterior.

### score_v2_status

Enquanto o novo modelo territorial não estiver calibrado:

- `blocked`;
- `under_calibration`;
- `experimental`.

O valor `validated` somente pode ser utilizado após backtesting, revisão epidemiológica, revisão estatística e aprovação humana registrada.

## Indicadores futuros

Após reconstrução do histórico:

- baseline sazonal;
- excesso sobre baseline;
- razão de tendência;
- positividade laboratorial;
- composição viral;
- atraso de notificação;
- completude;
- oportunidade;
- confiança do sinal;
- pressão assistencial;
- nível de atividade calibrado historicamente.

Todos deverão possuir fórmula, fonte, periodicidade, limitações e teste de reprodução antes de entrar no painel público.
