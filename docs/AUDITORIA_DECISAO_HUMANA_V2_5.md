# Auditoria de Decisão Humana — v2.5

## Finalidade

Registrar, validar e acompanhar decisões humanas tomadas a partir da revisão operacional, mantendo separação explícita entre:

- sugestão do sistema;
- decisão humana;
- follow-up;
- eventual ação externa.

O sistema não presume que uma decisão foi executada no mundo real.

## Entradas

A v2.5 utiliza:

- fila municipal v2.2;
- sugestões de ações v2.2, quando aplicável;
- metadata/snapshot de origem;
- registro preenchido por pessoa responsável.

## Escopos de decisão

### queue

Decisão referente à fila municipal como um todo.

### action

Decisão referente a uma sugestão específica de ação.

Nesse caso, action_id precisa existir nas sugestões da mesma localidade.

## Decisões permitidas

- continue_monitoring;
- request_data_validation;
- request_epi_investigation;
- request_laboratory_review;
- request_assistance_coordination;
- request_multidisciplinary_review;
- closed_no_escalation.

Esses estados são registros de workflow.

Eles não:

- executam investigação;
- acionam serviço automaticamente;
- notificam município automaticamente;
- prescrevem conduta;
- alteram classificação clínica;
- comprovam que uma ação externa ocorreu.

## Identificador de decisão

Cada registro validado recebe decision_record_id determinístico, derivado de snapshot, município, fila, escopo, action_id quando existir, horário da revisão e decision_status.

## Follow-up

Uma decisão pode definir follow_up_required=true.

Nesse caso são obrigatórios prazo e papel responsável.

Eventos humanos podem ser registrados como acknowledged, in_progress, completed ou cancelled.

O estado calculado pode ser not_required, open, overdue, completed ou cancelled.

overdue significa prazo de workflow vencido. Não significa aumento de risco epidemiológico.

## Proteções

Toda decisão validada mantém:

- decision_recorded_by_human = true;
- automatic_execution_enabled = false;
- patient_level_decision_enabled = false;
- clinical_prescription_enabled = false;
- decision_is_not_proof_of_execution = true.

Todo follow-up mantém:

- follow_up_event_recorded_by_human = true;
- automatic_execution_enabled = false;
- follow_up_event_is_not_proof_of_external_action = true;
- follow_up_state_is_not_risk = true.

## Relação com v2.4

A v2.4 mede estabilidade da fila entre vintages.

A v2.5 registra a resposta humana ao workflow.

Essas duas dimensões podem ser comparadas analiticamente, mas uma não deve substituir a outra.
