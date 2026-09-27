# v2.8 — Avaliação Formal de Propostas de Mudança

## Finalidade

Registrar a avaliação humana formal das propostas v2.7 antes que qualquer alteração seja autorizada para uma branch de implementação.

## Princípio central

`approve_for_implementation_branch` não significa implementação.

Mesmo após aprovação:

- nenhuma regra é alterada automaticamente;
- nenhum threshold é alterado automaticamente;
- nenhum merge é executado automaticamente;
- nenhum deploy é executado automaticamente.

## Tipos de revisão

Para mudanças de lógica (`queue_rule`, `action_trigger`, `threshold`, `context_requirement`), a aprovação exige:

- case review = passed;
- revisão epidemiológica = passed;
- backtesting = passed;
- revisão estatística = passed;
- documentação = passed.

Para mudança apenas documental, backtesting e revisão estatística podem ser `not_applicable`, mas case review, epidemiologia e documentação precisam passar.

## Decisões finais

- approve_for_implementation_branch;
- reject;
- defer.

## Dados registrados

A avaliação inclui:

- proposal_id;
- proposal_type;
- evaluated_at;
- reviewer_role;
- status das revisões;
- referências de evidência;
- impact_summary;
- risk_summary;
- final_decision;
- decision_rationale;
- implementation_notes.

## Privacidade

Registrar somente `reviewer_role`.

Não armazenar nome, CPF, matrícula, e-mail ou identificador pessoal.

## Proteções

- proposal_is_not_change = true;
- decision_is_not_implementation = true;
- automatic_rule_change_enabled = false;
- automatic_threshold_change_enabled = false;
- automatic_merge_enabled = false;
- automatic_deploy_enabled = false;
- human_approval_required = true;
- personal_identifier_storage = false.

## Próximo gate

Uma proposta aprovada pode seguir somente para uma branch separada de implementação.

Nessa branch, a mudança precisa ser novamente testada, comparada e revisada antes de qualquer merge.
