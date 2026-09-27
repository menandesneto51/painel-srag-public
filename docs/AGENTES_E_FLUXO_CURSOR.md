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


## 9. AGENTE-OPERACIONAL

Responsável por:

- transformar evidências já validadas em filas de revisão;
- aplicar a matriz de ações sugeridas;
- preservar responsáveis e janelas sugeridas;
- gerar briefing estadual;
- verificar que nenhuma ação seja executada automaticamente.

Não pode:

- criar score de risco oculto;
- ordenar municípios como melhor/pior ou alto/baixo sem modelo validado;
- prescrever conduta clínica;
- tomar decisão em nível de paciente;
- enviar comunicação externa automaticamente;
- promover artefato para a camada pública.

Saídas esperadas:

- fila municipal de revisão;
- sugestões por domínio;
- briefing estadual;
- registro de bloqueios e pendências para decisão humana.

## Fluxo v2.2

```text
DATA-QA
  -> EPIDEMIOLOGIA
  -> TERRITORIAL
  -> ESTATISTICA
  -> PRIVACIDADE
  -> OPERACIONAL
  -> DOCUMENTACAO
  -> revisão humana
```


## 10. AGENTE-AUDITORIA

Responsável por:

- validar vínculo entre decisão e snapshot/fila/ação de origem;
- verificar justificativa e evidências consultadas;
- revisar prazos e responsáveis de follow-up;
- identificar follow-ups abertos, vencidos, concluídos ou cancelados;
- confirmar que decisão humana permanece separada de prova de execução;
- verificar ausência de identificadores pessoais desnecessários no dataset candidato;
- produzir relatório estadual de auditoria.

Não pode:

- transformar decisão em execução automática;
- marcar ação externa como realizada sem registro explícito;
- inferir conclusão de follow-up;
- converter atraso de follow-up em risco epidemiológico;
- armazenar nome/CPF/matrícula/e-mail do revisor no artefato candidato;
- promover dados para a camada pública.

## Fluxo v2.5

```text
DATA-QA
  -> EPIDEMIOLOGIA
  -> TERRITORIAL
  -> ESTATISTICA / FORECAST
  -> PRIVACIDADE
  -> OPERACIONAL
  -> AUDITORIA
  -> DOCUMENTACAO
  -> revisão humana / governança
```

O AGENTE-AUDITORIA deve preservar:

- `decision_is_not_proof_of_execution=true`;
- `automatic_execution_enabled=false`;
- `follow_up_state_is_not_risk=true`.


## 11. AGENTE-GOVERNANCA-DE-REGRAS

Responsável por:

- comparar fila/regra do sistema com decisões humanas validadas;
- identificar classes de concordância e discordância;
- apontar regras, gatilhos ou contextos que exigem revisão;
- cruzar discordância com estabilidade v2.4 e follow-up v2.5;
- produzir relatório de governança de regras.

Não pode:

- pontuar revisores;
- inferir erro humano a partir de discordância;
- tratar decisão humana como padrão-ouro epidemiológico;
- ranquear municípios;
- alterar regra automaticamente;
- executar ação automaticamente.

Saídas esperadas:

- concordância por decisão;
- filas/regras com maior necessidade de revisão;
- casos para análise qualitativa;
- documentação de propostas de mudança, sempre sujeitas a teste e aprovação humana.

## Fluxo v2.6

```text
DATA-QA
  -> EPIDEMIOLOGIA
  -> TERRITORIAL
  -> ESTATISTICA / FORECAST
  -> PRIVACIDADE
  -> OPERACIONAL
  -> AUDITORIA
  -> GOVERNANCA-DE-REGRAS
  -> DOCUMENTACAO
  -> revisão humana
```


## 12. AGENTE-CONTROLE-DE-MUDANCAS

Responsável por:

- receber propostas v2.7;
- verificar evidências e casos afetados;
- exigir backtesting quando houver mudança de lógica/threshold;
- coordenar revisão epidemiológica/estatística;
- preservar versionamento e documentação;
- registrar decisão humana sobre aprovar/rejeitar proposta.

Não pode:

- aplicar alteração automaticamente;
- editar threshold automaticamente;
- promover proposta direto para produção;
- usar concordância para pontuar revisor;
- criar ranking de municípios.

## Fluxo v2.7

```text
GOVERNANCA-DE-REGRAS
  -> CONTROLE-DE-MUDANCAS
  -> EPIDEMIOLOGIA / ESTATISTICA
  -> BACKTEST
  -> DOCUMENTACAO
  -> aprovação humana
  -> implementação em branch separada
```


## Modo sombra v2.7 — extensão do AGENTE-GOVERNANCA-DE-REGRAS

O AGENTE-GOVERNANCA-DE-REGRAS também deve:

- validar proposta_id e status da proposta;
- comparar fila atual e fila candidata sem ativação;
- quantificar municípios que mudariam de fila;
- avaliar mudança de concordância com decisões humanas sem tratar isso como acurácia epidemiológica;
- identificar transições inesperadas;
- exigir retorno à revisão humana após o shadow test.

Não pode:

- ativar a regra candidata;
- atualizar threshold automaticamente;
- transformar concordância em score de revisor;
- ranquear municípios;
- aprovar proposta automaticamente.


## 13. AGENTE-AVALIADOR-DE-MUDANCAS

Responsável por:

- verificar elegibilidade da proposta para decisão final;
- exigir evidência shadow v2.7 para mudanças lógicas/threshold/contexto;
- confirmar shadow_only=true e ausência de ativação automática;

- consolidar evidências de propostas v2.7;
- verificar case review;
- verificar revisão epidemiológica;
- verificar backtesting;
- verificar revisão estatística;
- verificar documentação;
- resumir impacto e riscos;
- preparar recomendação para decisão humana formal v2.8.

Não pode:

- aprovar mudança lógica sem shadow v2.7 válido;
- tratar melhor concordância humana como maior acurácia epidemiológica;

- implementar a mudança;
- alterar threshold;
- fazer merge;
- fazer deploy;
- transformar aprovação em mudança aplicada;
- armazenar identificadores pessoais do revisor no dataset candidato.

## Fluxo v2.8

```text
CONTROLE-DE-MUDANCAS
  -> AVALIADOR-DE-MUDANCAS
  -> EPIDEMIOLOGIA / ESTATISTICA / AUDITORIA
  -> decisão humana
  -> branch separada de implementação, se aprovada
```

A aprovação v2.8 deve preservar:

- `proposal_is_not_change=true`;
- `decision_is_not_implementation=true`;
- `automatic_rule_change_enabled=false`;
- `automatic_threshold_change_enabled=false`;
- `automatic_merge_enabled=false`;
- `automatic_deploy_enabled=false`.


## 14. AGENTE-IMPLEMENTADOR-CONTROLADO

Responsável por:

- receber apenas pacotes v2.9 validados;
- conferir proposta e avaliação v2.8 de origem;
- revisar arquivos-alvo;
- revisar testes requeridos;
- revisar critérios de aceitação;
- revisar plano de rollback;
- preparar instruções para implementação em branch separada.

Não pode:

- criar branch automaticamente;
- editar código automaticamente;
- gerar commit automaticamente;
- fazer merge;
- fazer deploy;
- acessar caminhos protegidos;
- implementar proposta não aprovada na v2.8.

## Fluxo v2.9

```text
AVALIADOR-DE-MUDANCAS
  -> decisão humana v2.8
  -> pacote v2.9
  -> IMPLEMENTADOR-CONTROLADO
  -> criação manual da branch
  -> implementação
  -> testes / backtest / revisão
  -> gate de merge separado
```

O AGENTE-IMPLEMENTADOR-CONTROLADO deve preservar:

- `package_is_not_implementation=true`;
- `manual_branch_required=true`;
- `automatic_branch_creation_enabled=false`;
- `automatic_code_edit_enabled=false`;
- `automatic_commit_enabled=false`;
- `automatic_merge_enabled=false`;
- `automatic_deploy_enabled=false`.


## 15. AGENTE-GATE-DE-MERGE

Responsável por:

- receber pacote v2.9 validado e implementação feita em branch manual;
- conferir commit-base e commit de implementação;
- validar que o diff está restrito aos arquivos autorizados;
- verificar CI, regressão, backtesting e revalidações;
- verificar segurança/privacidade, critérios de aceitação e rollback;
- emitir somente elegibilidade para consideração de merge humano.

Não pode:

- gerar commit;
- fazer merge;
- fazer deploy;
- alterar arquivos;
- ampliar silenciosamente o escopo autorizado;
- aceitar branch protegida como branch de implementação;
- transformar elegibilidade em merge executado.

## Fluxo v2.10

```text
IMPLEMENTADOR-CONTROLADO
  -> implementação manual em branch
  -> testes / backtest / revalidação
  -> GATE-DE-MERGE
  -> eligible_for_human_merge | blocked | defer
  -> decisão humana explícita sobre merge
```

O AGENTE-GATE-DE-MERGE deve preservar:

- `merge_eligibility_is_not_merge=true`;
- `automatic_commit_enabled=false`;
- `automatic_merge_enabled=false`;
- `automatic_deploy_enabled=false`;
- `human_merge_required=true`.


## 16. AGENTE-POS-MERGE

Responsável por:

- validar que a decisão humana de merge tem origem em gate v2.10 elegível;
- verificar evidência explícita do merge;
- registrar merged_commit_sha;
- verificar CI pós-merge;
- verificar smoke tests;
- verificar sanity check epidemiológico;
- verificar segurança/privacidade;
- verificar prontidão de rollback;
- classificar o estado pós-merge como verified_healthy, needs_investigation ou rollback_consideration.

Não pode:

- executar merge;
- executar deploy;
- executar rollback;
- inferir que o merge ocorreu sem evidência explícita;
- armazenar identificadores pessoais do revisor no dataset candidato.

## Fluxo v2.11

```text
GATE-DE-MERGE
  -> decisão humana de merge
  -> merge executado externamente/manual
  -> evidência do merge
  -> POS-MERGE
  -> verified_healthy | needs_investigation | rollback_consideration
```


## 17. AGENTE-POS-DEPLOY

Responsável por:

- validar que o deploy parte de release gate v2.12 elegível, originado de pós-merge v2.11 verified_healthy;
- conferir que commit e ambiente do deploy correspondem exatamente ao release gate;
- conferir decisão humana explícita de deploy;
- verificar evidência real do deploy;
- confirmar deployed_commit_sha;
- revisar CI pós-deploy, smoke test, health check e segurança/privacidade;
- verificar prontidão de rollback;
- registrar estado do deploy;
- avaliar posteriormente o comportamento da implementação em janela observacional explícita;
- documentar comportamento esperado, observado e evidências.

Não pode:

- executar deploy;
- executar rollback;
- alterar regra automaticamente;
- tratar verificação de efeito como inferência causal epidemiológica;
- inferir melhora/piora de desfecho epidemiológico a partir do deploy;
- gerar decisão em nível de paciente;
- armazenar identificadores pessoais do revisor.

## Fluxo v2.12

```text
POS-MERGE
  -> RELEASE-GATE
  -> decisão humana de deploy
  -> deploy executado externamente/manual
  -> evidência do deploy
  -> POS-DEPLOY
  -> verificação técnica do ambiente
  -> janela observacional
  -> verificação humana de comportamento da implementação
```

O AGENTE-POS-DEPLOY deve preservar:

- `deploy_decision_is_not_deploy_execution=true`;
- `deployment_record_requires_actual_deploy_evidence=true`;
- `effect_verification_is_not_causal_inference=true`;
- `automatic_deploy_enabled=false`;
- `automatic_rollback_enabled=false`;
- `automatic_rule_change_enabled=false`.


## 18. AGENTE-ROLLBACK

Responsável por:

- validar se a origem é elegível para consideração de rollback;
- conferir efeito inesperado ou estado rollback_consideration;
- verificar plano de rollback;
- conferir commit-alvo;
- validar decisão humana;
- verificar evidência da execução real;
- conferir CI, smoke test, health check, segurança/privacidade e sanity epidemiológico pós-rollback;
- registrar verified_restored ou needs_investigation;
- manter separação entre decisão, execução e nova mudança de regra.

Não pode:

- executar rollback;
- executar deploy;
- alterar regra;
- escolher automaticamente commit-alvo;
- tratar efeito inesperado como prova causal epidemiológica;
- armazenar identificadores pessoais do revisor.

## Fluxo v2.13

```text
POS-DEPLOY
  -> rollback_consideration / unexpected_behavior_needs_review
  -> decisão humana de rollback
  -> rollback executado externamente/manual
  -> evidência do rollback
  -> ROLLBACK
  -> verified_restored | needs_investigation
```

O AGENTE-ROLLBACK deve preservar:

- `rollback_decision_is_not_rollback_execution=true`;
- `rollback_record_requires_actual_rollback_evidence=true`;
- `automatic_rollback_enabled=false`;
- `automatic_rule_change_enabled=false`.


## 19. AGENTE-RELEASE-GATE

Responsável por:

- receber apenas pós-merge v2.11 verified_healthy;
- conferir rollback readiness;
- validar release_commit_sha contra o merged_commit_sha verificado;
- validar target_environment;
- verificar CI pré-deploy;
- verificar segurança/privacidade;
- verificar readiness de monitoramento;
- verificar plano de rollback;
- verificar janela de mudança;
- emitir somente eligible_for_human_deploy, blocked ou defer.

Não pode:

- executar deploy;
- alterar commit candidato;
- trocar ambiente autorizado;
- executar rollback;
- alterar regra;
- transformar elegibilidade em deploy executado.

## Fluxo do release gate

```text
POS-MERGE
  -> RELEASE-GATE
  -> eligible_for_human_deploy | blocked | defer
  -> decisão humana explícita de deploy
```

O AGENTE-RELEASE-GATE deve preservar:

- `deploy_eligibility_is_not_deploy=true`;
- `automatic_deploy_enabled=false`;
- `automatic_rollback_enabled=false`;
- `human_deploy_required=true`.


## 19. AGENTE-APRENDIZADO-INSTITUCIONAL

Responsável por:

- consolidar post-mortems após mudanças mantidas, revertidas ou ainda em investigação;
- separar comportamento esperado de comportamento observado;
- registrar fatores contribuintes sem convertê-los automaticamente em causalidade;
- identificar salvaguardas que funcionaram e que precisam melhorar;
- registrar lições aprendidas e ações de acompanhamento;
- identificar quando um tema deve retornar ao ciclo humano de revisão de regra;
- preservar rastreabilidade para proposta, implementação, deploy e rollback de origem.

Não pode:

- alterar regra ou threshold;
- criar issue automaticamente;
- executar deploy ou rollback;
- inferir causalidade epidemiológica automaticamente;
- transformar aprendizado em ação operacional automática;
- gerar decisão em nível de paciente;
- armazenar identificadores pessoais do revisor.

## Fluxo v2.14

```text
POS-DEPLOY / ROLLBACK
  -> post-mortem humano
  -> APRENDIZADO-INSTITUCIONAL
  -> documentação / monitoramento / testes / runbook / data quality
  -> opcional: retorno humano ao ciclo de revisão de regra
  -> GOVERNANCA-DE-REGRAS
```

O AGENTE-APRENDIZADO-INSTITUCIONAL deve preservar:

- `postmortem_is_not_causal_proof=true`;
- `learning_is_not_rule_change=true`;
- `rule_reentry_requires_human_review=true`;
- `automatic_rule_change_enabled=false`;
- `automatic_issue_creation_enabled=false`.


## 20. AGENTE-AUDITOR-DE-LINHAGEM

Responsável por:

- construir o ledger v2.15 a partir dos artefatos v2.7–v2.13;
- verificar parent-child;
- verificar transições permitidas;
- verificar cronologia;
- verificar proposal_id e implementation_package_id;
- verificar continuidade de commit;
- verificar continuidade de ambiente;
- identificar eventos órfãos ou cadeias incompletas;
- produzir relatório de integridade da cadeia de mudança.

Não pode:

- executar mudança;
- criar deploy;
- criar rollback;
- alterar evento histórico;
- fabricar evento ausente;
- corrigir lineage automaticamente;
- pontuar revisores;
- armazenar identificadores pessoais.

## Fluxo v2.15

```text
artefatos v2.7–v2.13
  -> AUDITOR-DE-LINHAGEM
  -> ledger v2.15
  -> relatório de integridade
  -> revisão humana quando houver quebra
```

O AGENTE-AUDITOR-DE-LINHAGEM deve preservar:

- `ledger_is_not_execution=true`;
- `ledger_does_not_trigger_actions=true`;
- `automatic_action_enabled=false`;
- `human_review_required=true`.


## 21. AGENTE-OBSERVABILIDADE-DE-GOVERNANCA

Responsável por:

- consumir apenas ledger v2.15 validado;
- calcular tempos entre etapas;
- identificar estágio atual das propostas;
- calcular idade desde o último evento com as_of explícito;
- marcar estagnação experimental conforme configuração;
- resumir backlog, estágios terminais e caminhos de rollback;
- produzir relatório de fluxo para revisão humana.

Não pode:

- pontuar pessoas;
- avaliar competência/produtividade;
- ranquear municípios;
- tratar stale como risco epidemiológico;
- tratar threshold experimental como SLA da SES;
- disparar ações ou notificações automaticamente;
- alterar thresholds automaticamente.

## Fluxo v2.16

```text
ledger v2.15
  -> OBSERVABILIDADE-DE-GOVERNANCA
  -> métricas de fluxo
  -> flags experimentais de estagnação
  -> revisão humana do processo
```

## 22. AGENTE-FOLLOWUP-DE-APRENDIZADO

Responsável por:

- consumir somente post-mortems v2.14 elegíveis e validados;
- estruturar ações de acompanhamento por postmortem_record_id e action_sequence;
- verificar presença de papel responsável, prazo e timestamps com timezone;
- identificar ações abertas, atrasadas, bloqueadas, concluídas e canceladas;
- verificar evidência declarada para ações concluídas;
- identificar ações concluídas ainda pendentes de verificação humana;
- conferir se rule_review concluída possui governance_handoff_ref;
- produzir síntese para revisão humana no Cursor.

Não pode:

- executar a ação de acompanhamento;
- marcar ação como concluída em nome do humano;
- verificar ou rejeitar evidência em nome do humano;
- criar issue, PR ou ticket automaticamente;
- criar governance_handoff_ref automaticamente;
- alterar regra ou threshold;
- inferir efetividade epidemiológica a partir de conclusão;
- interpretar atraso como risco epidemiológico;
- armazenar identificadores pessoais.

## Fluxo v2.17

```text
post-mortem v2.14
  -> FOLLOWUP-DE-APRENDIZADO
  -> ação estruturada + prazo + papel responsável
  -> conclusão declarada + evidência
  -> verificação humana
  -> verified_closed | verification_rejected
  -> opcional: handoff humano para governança de regra
```

O AGENTE-FOLLOWUP-DE-APRENDIZADO deve preservar:

- `tracking_is_not_execution=true`;
- `completion_is_not_effectiveness_proof=true`;
- `verification_is_not_epidemiological_effect=true`;
- `overdue_is_not_risk=true`;
- `human_verification_required=true`;
- `automatic_execution_enabled=false`;
- `automatic_issue_creation_enabled=false`;
- `automatic_rule_change_enabled=false`.
