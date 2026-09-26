# Agentes e fluxo de trabalho no Cursor — Painel SRAG v2

## Princípio

Os agentes funcionam como papéis especializados e auditáveis. Nenhum agente promove sozinho um snapshot para publicação.

## 1. AGENTE-DATA-QA

Responsável por:

- schema;
- tipos;
- duplicidades;
- missing;
- chaves;
- consistência de datas;
- reconciliação de contagens;
- comparação entre versões.

Saída esperada:

`reports/data_quality_<timestamp>.md`

Bloqueia o pipeline quando houver erro estrutural.

## 2. AGENTE-EPIDEMIOLOGIA

Responsável por:

- definição de caso e recortes;
- escolha da SE;
- interpretação de atraso;
- denominadores;
- taxas;
- silêncio epidemiológico;
- plausibilidade das tendências.

Não pode corrigir dado por plausibilidade. Deve produzir hipótese e rastreabilidade.

## 3. AGENTE-TERRITORIAL

Responsável por:

- código IBGE;
- município;
- região de saúde/RGI quando aplicável;
- joins territoriais;
- população;
- outliers territoriais;
- comparação entre municípios de portes distintos.

Regra crítica: nunca usar nome do município como chave primária quando houver código oficial disponível.

## 4. AGENTE-ESTATISTICA

Responsável por:

- OR e IC95%;
- modelos ajustados;
- tratamento de missing;
- estabilidade de estimativas;
- pequenos números;
- validação de intervalos;
- documentação da população analítica.

Não deve interpretar associação como causalidade.

## 5. AGENTE-FORECAST

Responsável por:

- nowcasting;
- forecast;
- horizonte;
- backtesting;
- erro;
- intervalo de incerteza;
- comparação com baseline.

Um forecast sem backtesting deve ser marcado como experimental.

## 6. AGENTE-PRIVACIDADE

Responsável por:

- granularidade;
- pequenas células;
- risco de reidentificação;
- conteúdo do repositório;
- segredos;
- separação entre ambiente interno e público.

Deve bloquear qualquer tentativa de versionar microdados ou credenciais.

## 7. AGENTE-DOCUMENTACAO

Responsável por:

- metodologia;
- dicionário de indicadores;
- fontes;
- changelog;
- proveniência;
- notas de versão.

Toda mudança epidemiológica deve atualizar documentação correspondente.

## 8. AGENTE-ORQUESTRADOR

Ordem padrão:

```text
DATA-QA
  -> EPIDEMIOLOGIA
  -> TERRITORIAL
  -> ESTATISTICA / FORECAST
  -> PRIVACIDADE
  -> DOCUMENTACAO
  -> gate final
```

O orquestrador não ignora bloqueios.

## Fluxo P0 no Cursor

### Etapa A — reconstrução populacional

1. obter estimativas municipais oficiais IBGE 2026;
2. preservar código IBGE;
3. filtrar Mato Grosso;
4. garantir um registro por município;
5. validar 142 municípios;
6. registrar fonte, data de referência e data de obtenção.

### Etapa B — reconstrução SRAG

1. obter banco vivo SIVEP-Gripe 2026;
2. registrar identificador/data do recurso;
3. filtrar residência/notificação conforme definição do indicador;
4. não misturar conceitos sem nomeá-los;
5. gerar agregados por SE e território.

### Etapa C — incidência

Calcular:

`incidencia_100k = numerador / populacao * 100000`

Depois comparar o valor recalculado com o artefato anterior e gerar relatório das diferenças.

### Etapa D — score

Somente recalcular score após validar seus componentes. Registrar:

- fórmula;
- pesos;
- normalização;
- limites;
- versão.

### Etapa E — publicação

Executar:

```bash
python scripts/validate_public_data.py
python -m unittest discover -s tests -v
```

Somente após aprovação humana alterar:

```json
"publication_status": "validated"
```

## Prompt operacional para Cursor

> Trabalhe no Painel SRAG Público v2 seguindo integralmente `.cursor/rules/painel-srag-v2.mdc`. Execute o P0 sem alterar silenciosamente nenhum dado. Reconstrua primeiro a referência populacional oficial do IBGE 2026 por código municipal; depois reconstrua os agregados SRAG 2026 a partir do SIVEP-Gripe, mantendo proveniência e data de extração. Recalcule incidências, gere relatório de diferenças contra o snapshot legado e só então avalie o score territorial. Preserve a separação entre camada interna e camada pública. Não publique microdados. Rode os agentes DATA-QA, EPIDEMIOLOGIA, TERRITORIAL, ESTATISTICA, FORECAST, PRIVACIDADE e DOCUMENTACAO, registrando bloqueios e evidências. Não mude publication_status para validated enquanto houver erro nos gates.
