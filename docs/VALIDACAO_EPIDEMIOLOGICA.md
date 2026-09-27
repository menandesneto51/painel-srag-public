# Protocolo de Validação Epidemiológica — P0

## Objetivo

Impedir que inconsistências estruturais, temporais ou de denominador cheguem silenciosamente à interface pública.

## Gates

### G0 — Segurança e publicabilidade

Falha se houver:

- colunas identificadoras individuais;
- microdados;
- arquivos de banco local;
- credenciais/segredos;
- granularidade incompatível com publicação segura.

### G1 — Estrutura

Verificar:

- presença de todos os arquivos obrigatórios;
- schema esperado;
- tipos de dados;
- duplicidades na chave declarada;
- campos críticos nulos.

### G2 — Coerência temporal

Verificar:

- `generated_at` válido;
- ano do metadata compatível com o dataset;
- `stable_week` entre 1 e 53;
- `stable_week <= max(SE observada)`;
- forecasts posteriores à data de corte;
- referência semanal existente no arquivo semanal.

### G3 — Denominadores e taxas

Antes de liberar risco municipal:

- anexar população IBGE 2026 por código municipal;
- garantir join 1:1 por código IBGE;
- não usar nome municipal como chave primária;
- recalcular todas as taxas;
- comparar taxa publicada e taxa recalculada com tolerância numérica definida;
- bloquear linhas sem população válida.

### G4 — Consistência aritmética

Exemplos:

- UTI <= hospitalizados;
- óbitos <= registros elegíveis ao desfecho;
- percentuais entre 0 e 100 quando aplicável;
- IC95% inferior <= estimativa <= IC95% superior;
- contagens não negativas.

### G5 — Plausibilidade epidemiológica

Revisar:

- saltos abruptos;
- municípios extremos;
- pequenos denominadores;
- mudanças na testagem;
- atraso de digitação;
- proporção de registros sem encerramento;
- inconsistência entre tendência estadual e territorial.

Plausibilidade gera alerta para revisão; não deve substituir uma regra epidemiológica formal.

## Bloqueadores já identificados no snapshot atual

1. `metadata_public.json` declara `stable_week = 47`, enquanto o arquivo semanal atualmente termina em SE 18.
2. Os KPIs semanais usam nomes diferentes dos esperados na interface:
   - `hospitalizados` vs. `hospitalizacoes`;
   - `tx_uti_percent` vs. `taxa_uti_hosp_percent`.
3. O arquivo de risco não contém população/código IBGE suficientes para auditar as incidências publicadas.
4. Existem taxas municipais incompatíveis com as respectivas contagens, exigindo reprocessamento do denominador.
5. A interface mistura valor acumulado com delta calculado entre semanas isoladas.

## Regra de liberação

O pipeline só poderá definir:

```json
"publication_status": "validated"
```

quando G0-G4 forem aprovados e G5 tiver revisão epidemiológica registrada.

Estados permitidos:

- `blocked`
- `under_review`
- `validated`
- `superseded`

## Responsabilidades dos agentes

Os agentes podem:

- executar QA;
- detectar anomalias;
- comparar versões;
- sugerir investigação;
- gerar resumo técnico.

Os agentes não podem:

- corrigir automaticamente numeradores/denominadores sem rastreabilidade;
- declarar um dado epidemiologicamente válido apenas por plausibilidade;
- promover um snapshot para `validated` sem o gate previsto.
