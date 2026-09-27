# SES_DATA_CATALOG — configuração do preflight

## Objetivo

O `painel-srag-public` é público. O preflight `SES_DATA_CATALOG` é obrigatório para mudanças de dados, mas os inventários internos da SES-MT não devem ser copiados para este repositório.

O projeto contém apenas um launcher público. O motor canônico e os inventários autorizados permanecem fora do repositório público.

## Comando canônico

```bash
python scripts/catalogo_ses.py --query "internações por SRAG, capacidade hospitalar e município"
```

No PowerShell:

```powershell
.\scripts\catalogo-ses.ps1 -Query "internações por SRAG, capacidade hospitalar e município"
```

## Configuração

Defina no ambiente local autorizado:

```text
SES_DATA_CATALOG_AGENT_ROOT=<caminho do clone canônico vigia-vsr>
SES_DATA_CATALOG_ROOT=<caminho autorizado dos inventários>
```

`SES_DATA_CATALOG_ROOT` pode ser omitido quando o próprio motor canônico já resolve os inventários no workspace.

No PowerShell, opcionalmente:

```text
SES_DATA_CATALOG_PYTHON=<interpretador Python>
```

## Ordem de resolução do motor

1. `--agent-root`;
2. `SES_DATA_CATALOG_AGENT_ROOT`;
3. `agents/ses_data_catalog/catalog_agent.py` local;
4. workspace irmão `../vigia-vsr/agents/ses_data_catalog/catalog_agent.py`.

Não há download automático nem bootstrap de dados internos.

## Clone limpo

O launcher é executável mesmo sem o catálogo. Se o motor canônico não estiver disponível, retorna:

```json
{
  "status": "configuration_required",
  "preflight_complete": false,
  "can_create_new_source": false
}
```

Esse retorno é um bloqueio de governança. O Cursor deve interromper criação de nova fonte/coletor/API/ETL/tabela/indicador/linkage até a configuração ser corrigida.

Para transformar ausência de configuração em erro de processo:

```bash
python scripts/catalogo_ses.py --query "<consulta>" --strict-config
```

## Gate do catálogo

Com preflight completo, o motor canônico expõe `preflight_decision.status`:

- `reuse_existing`: reutilizar/validar fonte existente; nova fonte bloqueada.
- `refresh_catalog`: atualizar inventários e repetir a busca; nova fonte bloqueada.
- `review_new_source`: catálogo completo sem candidato forte; autoriza somente revisão formal de governança.

Nenhum estado implementa, conecta ou publica uma nova fonte automaticamente.

## Self-test

```bash
python scripts/catalogo_ses.py --self-test
```

O self-test valida apenas o launcher e não substitui a consulta ao catálogo.

## Segurança e LGPD

- não copiar inventários internos para este repositório público;
- não expor PII, microdados ou credenciais;
- `possible_pii` deve permanecer apenas como classificação de metadado;
- ausência de match em catálogo parcial não prova ausência de dado;
- nenhuma nova fonte é autorizada automaticamente pelo agente.

## Cursor

A regra `.cursor/rules/ses-data-catalog.mdc` é `alwaysApply`.

Fluxo:

`Cursor -> SES_DATA_CATALOG -> DATA_GUARDIAN/DATAOPS -> implementação -> testes -> revisão humana`.
