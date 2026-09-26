# Vintages agregados SIVEP

Esta pasta armazena apenas snapshots **agregados** usados para medir revisão do banco vivo ao longo do tempo.

Estrutura esperada:

```text
vintages/sivep/
  YYYY-MM-DD/
    weekly.csv
    metadata.json
```

Regras:

- não armazenar microdados;
- usar a data do recurso/snapshot;
- não sobrescrever vintage existente sem justificar;
- manter hash e proveniência;
- usar `scripts/capture_vintage.py`;
- executar `scripts/backtest_vintages.py` quando houver pelo menos três vintages.

O último vintage é apenas referência operacional; ele também pode sofrer revisão futura.
