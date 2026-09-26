# Baseline Histórico SRAG — P2

## Fonte

OpenDataSUS / SIVEP-Gripe, recursos oficiais 2019–2026.

O portal informa que:

- o SIVEP-Gripe é o sistema oficial para casos e óbitos por SRAG;
- 2019–2024 estão congelados;
- o banco corrente é atualizado semanalmente;
- a vigilância foi ampliada a partir de 2020 com a pandemia de covid-19.

Fonte:
https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026

## Princípio de comparabilidade

A v2 **não mistura automaticamente 2019–2026 em um único baseline**.

O usuário/pipeline deve informar explicitamente os anos comparáveis:

```bash
python scripts/build_historical_baseline.py \
  --baseline-years 2023,2024,2025
```

A seleção precisa ser justificada na análise.

## Primeira camada: estado

O baseline inicial é estadual e baseado em contagens semanais. Isso evita usar população 2026 como denominador histórico.

Indicadores:

- casos;
- hospitalizações;
- UTI;
- óbitos;
- curas.

## Estatísticas robustas por SE

Para cada semana epidemiológica e conjunto de anos selecionado:

- mediana;
- Q25;
- Q75;
- MAD;
- mínimo;
- máximo;
- número de anos disponíveis.

Nenhum limiar de risco é produzido nesta etapa.

## Municipal

Baseline municipal por taxa permanece bloqueado até:

1. obter denominadores populacionais anuais;
2. avaliar mudanças territoriais/códigos;
3. harmonizar eventuais alterações de limites/municípios;
4. validar estabilidade em pequenos números.

## Próxima etapa

Usar o baseline como entrada para um módulo separado de anomalias com:

- excesso observado;
- incerteza;
- robustez a MAD zero;
- persistência temporal;
- confiança do sinal;
- backtesting.
