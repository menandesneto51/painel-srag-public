# v2.12 — Deploy Humano e Verificação Pós-Deploy

## Objetivo

Separar explicitamente:

1. decisão humana de realizar deploy;
2. evidência de que o deploy realmente ocorreu;
3. verificação posterior do comportamento da implementação.

A v2.12 não executa deploy, rollback ou alteração de regra.

## Pré-condição

Somente registros v2.11 com:

`post_merge_state = verified_healthy`

podem seguir para decisão de deploy.

## Decisão de deploy

Estados:

- approve_human_deploy;
- reject_deploy;
- defer_deploy.

Regra:

`deploy_decision_is_not_deploy_execution = true`

## Registro de deploy

Somente `approve_human_deploy` pode originar registro de deploy.

São obrigatórios:

- ambiente;
- commit implantado;
- referência de evidência do deploy;
- CI pós-deploy;
- smoke test;
- health check;
- segurança/privacidade;
- prontidão de rollback;
- notas humanas.

O `deployed_commit_sha` deve corresponder ao `merged_commit_sha`.

## Verificação de efeito

A verificação observa o **comportamento da implementação/regra**, não causalidade epidemiológica.

Estados:

- implementation_behavior_verified;
- no_material_behavior_change;
- unexpected_behavior_needs_review;
- insufficient_observation_window.

Regra central:

`effect_verification_is_not_causal_inference = true`

Exemplo: uma mudança de fila pode ser verificada quanto à distribuição de filas, concordância de workflow e comportamento de regressão. Isso não permite afirmar que a mudança causou melhora ou piora de hospitalizações, óbitos ou circulação viral.

## Proteções

Sempre:

- automatic_deploy=false;
- automatic_rollback=false;
- automatic_rule_change=false;
- patient_level_decision=false;
- personal_identifier_storage=false;
- revisão humana obrigatória.
