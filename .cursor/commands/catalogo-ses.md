# Buscar no Catálogo Mestre SES-MT

Use o launcher cross-platform como comando canônico no Cursor:

```bash
python scripts/catalogo_ses.py --query "<necessidade de dados>"
```

No PowerShell, o wrapper permanece disponível:

```powershell
.\scripts\catalogo-ses.ps1 -Query "<necessidade de dados>"
```

Interprete o retorno antes de qualquer implementação:

- `status=ok` e `preflight_complete=true`: revisar `evidence.catalog_health`, candidatos, campos, sensibilidade e limitações.
- `status=configuration_required`: **não** criar fonte, coletor, scraper, API, ETL, tabela, indicador ou linkage. Configure o motor/catálogo canônico conforme `docs/SES_DATA_CATALOG_SETUP.md`.
- O preflight nunca autoriza automaticamente uma nova fonte.
- Não copie inventários internos ou PII para este repositório público.

Retorne: fontes, objetos, campos candidatos, flags de sensibilidade, `catalog_health`, ranking, limitações e próximo passo.
