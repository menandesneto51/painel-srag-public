# Fontes, base normativa e governança de dados

## 1. SIVEP-Gripe / Ministério da Saúde

O SIVEP-Gripe é o sistema oficial utilizado para registro dos casos e óbitos por SRAG. O Portal de Dados Abertos do SUS disponibiliza banco por ano epidemiológico e informa que o banco do ano corrente é vivo e atualizado periodicamente.

Fonte oficial:
https://dadosabertos.saude.gov.br/dataset/srag-2019-a-2026

A documentação operacional e as definições epidemiológicas devem seguir o Guia de Vigilância Integrada da Covid-19, Influenza e Outros Vírus Respiratórios de Importância em Saúde Pública, do Ministério da Saúde:

https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/guias-e-manuais/2024/guia-vigilancia-integrada-da-covid-19-influenza-e-outros-virus-respiratorios-de-importancia-em-saude-publica/view

## 2. População / IBGE

Para taxas municipais, utilizar como padrão a estimativa oficial do IBGE referente ao ano do indicador, identificando o município por código IBGE.

Fonte:
https://www.ibge.gov.br/estatisticas/sociais/populacao/9103-estimativas-de-populacao.html

Para 2026, o IBGE informa estimativas municipais com referência em 1º de julho de 2026.

## 3. LGPD

A Lei nº 13.709/2018 classifica dados referentes à saúde como dados pessoais sensíveis e define dado anonimizado e anonimização.

Texto oficial:
https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm

Aspectos relevantes para este projeto incluem:

- Art. 5º: conceitos de dado pessoal sensível, dado anonimizado e anonimização;
- Art. 7º: hipóteses gerais de tratamento, incluindo políticas públicas e tutela da saúde;
- Art. 11: tratamento de dados pessoais sensíveis, inclusive para políticas públicas e tutela da saúde;
- princípios de finalidade, adequação, necessidade, qualidade dos dados, transparência, segurança, prevenção e responsabilização.

A existência de base legal para tratamento institucional não elimina a necessidade de minimização, controles de acesso, segurança, rastreabilidade e avaliação da publicabilidade de cada produto.

## 4. Regra específica do repositório público

Este repositório deve operar como **camada de publicação**, não como repositório de microdados.

São proibidos no repositório:

- identificadores diretos;
- chaves que permitam reidentificação individual;
- bases nominais;
- arquivos internos de produção;
- credenciais;
- segredos;
- extratos de DW ou SIVEP com granularidade individual.

A publicação de agregados também deve avaliar risco de reidentificação por pequenas células, sobretudo quando houver combinação de município, idade, condição clínica, período e outros atributos.

## 5. Proveniência mínima obrigatória

Cada snapshot deve registrar:

- sistema-fonte;
- URL/referência da fonte;
- data de extração;
- data de geração;
- ano epidemiológico;
- última SE observada;
- SE considerada estável e regra empregada;
- versão do pipeline;
- versão do dicionário de variáveis;
- fonte/ano do denominador populacional;
- status de validação;
- hash ou identificador dos artefatos gerados.

## 6. Princípio de não substituição

Este documento orienta governança técnica do painel. Ele não substitui parecer jurídico, regras internas da SES-MT, política de segurança da informação, decisões do controlador ou orientação do encarregado de proteção de dados.
