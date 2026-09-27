# Inteligência Territorial SRAG v2.1

## Objetivo

Criar uma visão municipal multidimensional sem reduzir sinais heterogêneos a um score único.

Cada município passa a carregar, lado a lado:

- atividade/anomalia;
- tendência;
- confiança do sinal;
- silêncio epidemiológico;
- virologia;
- pressão assistencial, quando disponível e validada.

## Regra central

`composite_score = NA`

e

`operational_alert = false`

enquanto a v2.1 estiver em calibração.

## Virologia

A saída virológica municipal possui múltiplas linhas por vírus. Os denominadores de PCR são repetidos nessas linhas e **não podem ser somados diretamente**.

A v2.1:

1. deduplica `codigo_ibge + SE` para registros SRAG e resultados moleculares;
2. soma detecções por agente;
3. identifica agente predominante somente entre agentes nomeados;
4. mantém separada a categoria "Detectável sem agente codificado";
5. não calcula positividade específica por vírus sem denominador laboratorial validado.

Janela inicial: 2 SE até a `stable_week`.

## Pressão assistencial

Dimensão opcional e institucional.

Contrato mínimo:

- codigo_ibge;
- reference_week;
- pressure_status;
- validation_status;
- source_scope;
- pressure_evidence opcional.

O repositório público não depende de SISREG, ocupação nominal, regulação ou qualquer base restrita para funcionar.

Quando essa dimensão não estiver disponível:

`healthcare_pressure_available = false`

Isso não reduz nem aumenta automaticamente a atividade epidemiológica.

## Interpretação

Exemplo de perfil:

- sinal epidemiológico: elevado e crescente;
- confiança: alta;
- silêncio: atividade presente;
- virologia: Influenza A predominante;
- pressão assistencial: não disponível.

Esse perfil é informativo, mas ainda não equivale a "risco alto" nem a alerta operacional.

## Próxima calibração

A v2.1 deverá comparar retrospectivamente:

- sinais epidemiológicos;
- virologia;
- demanda assistencial;
- ocupação/UTI quando disponíveis;
- eventos reconhecidos;
- antecedência dos sinais;
- falsos positivos/negativos por porte municipal.

Somente após essa etapa será decidido se existe justificativa para um score composto. O padrão atual é permanecer multidimensional.
