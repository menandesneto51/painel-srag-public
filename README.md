# Painel SRAG Público — Mato Grosso

Painel público para monitoramento epidemiológico da Síndrome Respiratória Aguda Grave (SRAG), construído em Streamlit a partir de **dados agregados e publicáveis**.

> **Status da v2.0:** saneamento epidemiológico em andamento. O snapshot atualmente versionado foi gerado em 27/04/2026 e contém inconsistências conhecidas de metadados e denominadores municipais. Até a conclusão do P0, os indicadores territoriais de risco devem ser tratados como **não validados**.

## Objetivo

Disponibilizar uma camada pública, auditável e sem microdados identificáveis para acompanhar:

- notificações, hospitalizações, UTI, óbitos e evolução;
- circulação de vírus respiratórios;
- risco e silêncio epidemiológico municipal;
- nowcasting e forecasting;
- fatores associados a UTI e óbito;
- comparação temporal e territorial.

## Princípio arquitetural

A camada pública **não deve conter a base bruta do SIVEP-Gripe nem dados pessoais/sensíveis**.

Fluxo-alvo:

```text
Fonte oficial
  -> ingestão
  -> validação estrutural
  -> tratamento epidemiológico
  -> validação de denominadores
  -> agregação/anonimização
  -> validação para publicação
  -> artefatos públicos
  -> Streamlit
```

## Fontes oficiais

- Ministério da Saúde / OpenDataSUS — SIVEP-Gripe/SRAG:
  https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026
- IBGE — Estimativas da população municipal:
  https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html
- Lei nº 13.709/2018 — LGPD:
  https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm

## Execução local

```bash
pip install -r requirements.txt
streamlit run app_publico_streamlit.py
```

## Validação

```bash
python scripts/validate_public_data.py
```

Modo estrito, recomendado antes de publicação:

```bash
python scripts/validate_public_data.py --strict
```

Testes:

```bash
python -m unittest discover -s tests -v
```

## Regras de publicação

1. Nunca versionar microdados identificáveis ou pseudonimizados.
2. Todo indicador territorial com taxa deve registrar o denominador utilizado.
3. Incidência deve ser recalculável por `casos / população * 100000`.
4. O ano e a semana epidemiológica informados no metadata devem ser coerentes com os dados.
5. Forecasts devem carregar data de geração e horizonte.
6. OR deve informar população, desfecho, referência, método e se é bruto ou ajustado.
7. Resultados de agentes/IA são apoio analítico e não substituem validação epidemiológica humana.
8. O aplicativo deve sinalizar dados desatualizados ou inconsistentes; não deve mascará-los.

## Desenvolvimento no Cursor

O Cursor é o ambiente padrão de continuidade técnica deste projeto. As regras estão em:

`.cursor/rules/painel-srag-v2.mdc`

Prioridade corrente: **P0 — saneamento epidemiológico e contratos de dados**.

## Roadmap v2

- **P0:** metadados, denominadores, contratos dos KPIs, validação e testes.
- **P1:** pipeline reprodutível OpenDataSUS -> MT -> agregados públicos.
- **P2:** baseline, nowcast, anomalias, risco territorial e silêncio epidemiológico.
- **P3:** integração institucional com capacidade assistencial e outras fontes SES-MT.
- **P4:** agentes para QA, detecção de anomalias, síntese e apoio à decisão.
