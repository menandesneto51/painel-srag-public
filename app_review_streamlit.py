# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / "data_candidate"

st.set_page_config(
    page_title="SRAG MT v2.17 — Revisão Local",
    layout="wide",
)

st.title("SRAG MT v2.17 — Revisão Local")
st.error(
    "AMBIENTE DE REVISÃO. Os artefatos exibidos são candidatos/experimentais e "
    "não estão validados para publicação ou alerta operacional."
)
st.caption(
    "Este app lê somente data_candidate/. Ele não substitui app_publico_streamlit.py "
    "e não deve ser usado como endpoint público."
)


def read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_csv(path, dtype={"codigo_ibge": "string"})


def read_latest_nested_csv(
    root: Path,
    filename: str,
) -> tuple[pd.DataFrame | None, Path | None]:
    if not root.exists():
        return None, None
    candidates = [
        path for path in root.glob(f"*/{filename}")
        if path.is_file()
    ]
    if not candidates:
        return None, None
    selected = max(candidates, key=lambda path: path.stat().st_mtime)
    return (
        pd.read_csv(selected, dtype={"codigo_ibge": "string"}),
        selected,
    )


def show_missing(label: str, path: Path):
    st.info(f"{label} ainda não disponível: {path.relative_to(ROOT)}")


territorial_path = (
    CANDIDATE
    / "territorial_intelligence"
    / "territorial_intelligence_v2_1.csv"
)
signals_dir = CANDIDATE / "signals"
backtest_dir = CANDIDATE / "backtest"
operational_dir = CANDIDATE / "operational_v2_2"
legacy_operational_dir = CANDIDATE / "operational_review"
persistence_dir = CANDIDATE / "operational_persistence"
stability_dir = CANDIDATE / "operational_stability"
decision_audit_dir = CANDIDATE / "decision_audit_v2_5"
concordance_dir = CANDIDATE / "human_workflow_concordance_v2_6"
proposal_dir = CANDIDATE / "rule_change_proposals_v2_7"
shadow_dir = CANDIDATE / "rule_shadow_evaluation_v2_7"
evaluation_dir = CANDIDATE / "rule_change_evaluation_v2_8"
implementation_dir = CANDIDATE / "implementation_package_v2_9"
merge_gate_dir = CANDIDATE / "merge_gate_v2_10"
human_merge_dir = CANDIDATE / "human_merge_v2_11"
release_gate_dir = CANDIDATE / "release_deploy_gate_v2_12"
deployment_dir = CANDIDATE / "deployment_v2_12"
rollback_dir = CANDIDATE / "rollback_v2_13"
postmortem_dir = CANDIDATE / "postmortem_v2_14"
ledger_dir = CANDIDATE / "change_lifecycle_v2_15"
governance_observability_dir = CANDIDATE / "governance_observability_v2_16"
learning_action_followup_dir = CANDIDATE / "learning_action_followup_v2_17"

territorial = read_csv(territorial_path)
review_cards = read_csv(
    CANDIDATE / "territorial_intelligence" / "territorial_review_cards_v2_1.csv"
)
combined = read_csv(signals_dir / "combined_signals.csv")
confidence = read_csv(signals_dir / "signal_confidence.csv")
silence = read_csv(signals_dir / "silence_signals.csv")
baseline = read_csv(signals_dir / "baseline_seasonal.csv")
backtest = read_csv(backtest_dir / "anomaly_threshold_backtest.csv")
predictions = read_csv(backtest_dir / "anomaly_backtest_predictions.csv")
virology = read_csv(CANDIDATE / "virology_municipal_weekly_mt_2026.csv")
operational_queue = read_csv(operational_dir / "municipal_review_queue_v2_2.csv")
if operational_queue is None:
    operational_queue = read_csv(
        legacy_operational_dir / "operational_review_queue_v2_2.csv"
    )
operational_actions = read_csv(
    operational_dir / "operational_action_suggestions_v2_2.csv"
)
domain_review_queues = read_csv(
    operational_dir / "domain_review_queues_v2_2.csv"
)
operational_persistence = read_csv(
    persistence_dir / "operational_persistence_v2_3.csv"
)
operational_stability = read_csv(
    stability_dir / "operational_stability_v2_4.csv"
)
human_decisions_v25 = read_csv(
    decision_audit_dir / "human_decisions_validated_v2_5.csv"
)
follow_up_status_v25 = read_csv(
    decision_audit_dir / "follow_up_status_v2_5.csv"
)
follow_up_events_v25 = read_csv(
    decision_audit_dir / "follow_up_events_validated_v2_5.csv"
)
workflow_concordance_v26 = read_csv(
    concordance_dir / "human_workflow_concordance_v2_6.csv"
)
rule_change_proposals = read_csv(
    proposal_dir / "rule_change_proposals_v2_7.csv"
)
rule_shadow_evaluation_v27, rule_shadow_source_v27 = read_latest_nested_csv(
    shadow_dir,
    "rule_shadow_evaluation_v2_7.csv",
)
rule_change_evaluations_v28 = read_csv(
    evaluation_dir / "rule_change_evaluations_validated_v2_8.csv"
)
implementation_packages_v29 = read_csv(
    implementation_dir / "implementation_packages_validated_v2_9.csv"
)
merge_gate_records_v210 = read_csv(
    merge_gate_dir / "merge_gate_validated_v2_10.csv"
)
human_merge_decisions_v211 = read_csv(
    human_merge_dir / "human_merge_decisions_validated_v2_11.csv"
)
post_merge_records_v211 = read_csv(
    human_merge_dir / "post_merge_records_validated_v2_11.csv"
)
release_gate_records_v212 = read_csv(
    release_gate_dir / "release_deploy_gate_validated_v2_12.csv"
)
human_deploy_decisions_v212 = read_csv(
    deployment_dir / "human_deploy_decisions_validated_v2_12.csv"
)
deployment_records_v212 = read_csv(
    deployment_dir / "deployment_records_validated_v2_12.csv"
)
effect_verification_v212 = read_csv(
    deployment_dir / "effect_verification_validated_v2_12.csv"
)
rollback_decisions_v213 = read_csv(
    rollback_dir / "human_rollback_decisions_validated_v2_13.csv"
)
rollback_execution_v213 = read_csv(
    rollback_dir / "rollback_execution_validated_v2_13.csv"
)
postmortem_records_v214 = read_csv(
    postmortem_dir / "postmortem_validated_v2_14.csv"
)
change_lifecycle_v215 = read_csv(
    ledger_dir / "change_lifecycle_ledger_v2_15.csv"
)
governance_status_v216 = read_csv(
    governance_observability_dir / "governance_proposal_status_v2_16.csv"
)
governance_transitions_v216 = read_csv(
    governance_observability_dir / "governance_transition_metrics_v2_16.csv"
)
learning_action_followup_v217 = read_csv(
    learning_action_followup_dir / "learning_action_followup_validated_v2_17.csv"
)

tabs = st.tabs([
    "Inteligência territorial",
    "Sinais",
    "Confiança e silêncio",
    "Virologia",
    "Backtesting",
    "Revisão operacional v2.2",
    "Persistência v2.3",
    "Estabilidade v2.4",
    "Auditoria humana v2.5",
    "Concordância workflow × decisão v2.6",
    "Propostas e modo sombra v2.7",
    "Avaliação formal v2.8",
    "Pacotes de implementação v2.9",
    "Gate de merge v2.10",
    "Merge humano e pós-merge v2.11",
    "Deploy e efeito v2.12",
    "Rollback v2.13",
    "Post-mortem v2.14",
    "Ledger de mudanças v2.15",
    "Observabilidade de governança v2.16",
    "Follow-up de aprendizado v2.17",
])

with tabs[0]:
    st.subheader("Perfil territorial multidimensional")
    if territorial is None:
        show_missing("Inteligência territorial v2.1", territorial_path)
    else:
        st.metric("Municípios", territorial["codigo_ibge"].nunique())
        if "territorial_model_status" in territorial.columns:
            st.write(
                "**Status do modelo:**",
                ", ".join(sorted(territorial["territorial_model_status"].dropna().astype(str).unique()))
            )

        filter_options = ["Todos"]
        if "signal_status" in territorial.columns:
            filter_options += sorted(
                territorial["signal_status"].dropna().astype(str).unique().tolist()
            )
        selected = st.selectbox("Filtrar por sinal epidemiológico", filter_options)
        view = territorial.copy()
        if selected != "Todos":
            view = view.loc[view["signal_status"].astype(str) == selected]

        display_cols = [
            "codigo_ibge",
            "municipio",
            "signal_status",
            "anomaly_status",
            "trend_ratio",
            "signal_confidence",
            "silence_status",
            "virology_status",
            "virology_dominant_agent",
            "virology_dominant_agent_detections",
            "pressure_status",
            "healthcare_pressure_available",
            "territorial_model_status",
        ]
        st.dataframe(
            view[[c for c in display_cols if c in view.columns]],
            use_container_width=True,
            hide_index=True,
        )

        if review_cards is not None and not review_cards.empty:
            st.markdown("### Card explicável por município")
            municipalities = (
                review_cards[["codigo_ibge", "municipio"]]
                .drop_duplicates()
                .sort_values("municipio")
            )
            options = municipalities["municipio"].astype(str).tolist()
            selected_municipality = st.selectbox(
                "Município para revisão detalhada",
                options,
                key="review_card_municipality",
            )
            card = review_cards.loc[
                review_cards["municipio"].astype(str).eq(selected_municipality)
            ].iloc[0]
            st.write("**Evidências:**", card.get("evidence_summary", ""))
            tags = str(card.get("review_tags", "") or "")
            if tags:
                st.write("**Tags de revisão:**", ", ".join([x for x in tags.split("|") if x]))
            notes = str(card.get("review_notes", "") or "")
            if notes:
                st.write("**Notas:**", notes)
            st.caption(
                "Card experimental: requer revisão humana e não contém recomendação operacional automática."
            )

with tabs[1]:
    st.subheader("Atividade, tendência e anomalia")
    if combined is None:
        show_missing("Sinais combinados", signals_dir / "combined_signals.csv")
    else:
        latest_week = int(pd.to_numeric(combined["SE"], errors="coerce").max())
        latest = combined.loc[
            pd.to_numeric(combined["SE"], errors="coerce").eq(latest_week)
        ].copy()

        c1, c2 = st.columns(2)
        with c1:
            if "observed_value" in latest.columns:
                fig = px.histogram(
                    latest,
                    x="observed_value",
                    nbins=30,
                    title=f"Distribuição do observado — SE {latest_week}",
                )
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            if "trend_log2" in latest.columns:
                fig = px.histogram(
                    latest,
                    x="trend_log2",
                    nbins=30,
                    title=f"Distribuição da tendência log2 — SE {latest_week}",
                )
                st.plotly_chart(fig, use_container_width=True)

        st.dataframe(latest, use_container_width=True, hide_index=True)

    if baseline is not None:
        with st.expander("Baseline sazonal"):
            st.dataframe(baseline.head(500), use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Confiança do sinal e silêncio")
    c1, c2 = st.columns(2)

    with c1:
        if confidence is None:
            show_missing("Confiança do sinal", signals_dir / "signal_confidence.csv")
        else:
            counts = (
                confidence["signal_confidence"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("classe")
                .reset_index(name="municipios")
            )
            fig = px.bar(
                counts,
                x="classe",
                y="municipios",
                title="Confiança do sinal",
            )
            st.plotly_chart(fig, use_container_width=True)

    with c2:
        if silence is None:
            show_missing("Silêncio epidemiológico", signals_dir / "silence_signals.csv")
        else:
            counts = (
                silence["silence_status"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("classe")
                .reset_index(name="municipios")
            )
            fig = px.bar(
                counts,
                x="classe",
                y="municipios",
                title="Situação de silêncio",
            )
            st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.subheader("Virologia municipal")
    if virology is None:
        show_missing(
            "Virologia municipal semanal",
            CANDIDATE / "virology_municipal_weekly_mt_2026.csv",
        )
    else:
        virology["deteccoes"] = pd.to_numeric(
            virology["deteccoes"], errors="coerce"
        ).fillna(0)
        summary = (
            virology.groupby("virus", as_index=False)["deteccoes"]
            .sum()
            .sort_values("deteccoes", ascending=False)
        )
        fig = px.bar(
            summary.head(20),
            x="virus",
            y="deteccoes",
            title="Detecções virológicas — artefato candidato",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Detecção por agente não equivale a positividade específica. "
            "Os denominadores laboratoriais são tratados separadamente."
        )
        st.dataframe(summary, use_container_width=True, hide_index=True)

with tabs[4]:
    st.subheader("Backtesting P2")
    if backtest is None:
        show_missing(
            "Resumo de backtesting",
            backtest_dir / "anomaly_threshold_backtest.csv",
        )
    else:
        metric_cols = [
            "robust_z_threshold",
            "sensitivity",
            "specificity",
            "precision_ppv",
            "negative_predictive_value",
            "signal_rate",
            "event_rate",
        ]
        st.dataframe(
            backtest[[c for c in metric_cols if c in backtest.columns]],
            use_container_width=True,
            hide_index=True,
        )

        plot = backtest.copy()
        long = plot.melt(
            id_vars=["robust_z_threshold"],
            value_vars=[
                c for c in ("sensitivity", "specificity", "precision_ppv")
                if c in plot.columns
            ],
            var_name="metrica",
            value_name="valor",
        )
        if not long.empty:
            fig = px.line(
                long,
                x="robust_z_threshold",
                y="valor",
                color="metrica",
                markers=True,
                title="Desempenho por limiar robust-z",
            )
            st.plotly_chart(fig, use_container_width=True)

    if predictions is not None:
        with st.expander("Predições retrospectivas"):
            st.dataframe(predictions.head(1000), use_container_width=True, hide_index=True)

with tabs[5]:
    st.subheader("Revisão operacional v2.2")
    st.warning(
        "A v2.2 organiza revisão técnica e sugere itens para avaliação humana. "
        "Não é ranking de risco, não prescreve conduta e não executa ações automaticamente."
    )

    if operational_queue is None:
        show_missing(
            "Fila municipal v2.2",
            operational_dir / "municipal_review_queue_v2_2.csv",
        )
    else:
        if "review_queue" in operational_queue.columns:
            counts = (
                operational_queue["review_queue"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("fila")
                .reset_index(name="municipios")
            )
            fig = px.bar(
                counts,
                x="fila",
                y="municipios",
                title="Municípios por fila de revisão",
            )
            st.plotly_chart(fig, use_container_width=True)

        queues = ["Todas"]
        if "review_queue" in operational_queue.columns:
            queues += sorted(
                operational_queue["review_queue"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        selected_queue = st.selectbox(
            "Filtrar fila municipal",
            queues,
            key="operational_review_queue_filter",
        )
        view = operational_queue.copy()
        if selected_queue != "Todas":
            view = view.loc[
                view["review_queue"].astype(str).eq(selected_queue)
            ]

        display_cols = [
            "codigo_ibge",
            "municipio",
            "review_queue",
            "queue_description",
            "review_tags",
            "evidence_summary",
            "suggested_review_actions",
            "human_review_required",
            "automatic_execution_enabled",
            "queue_is_not_risk_rank",
        ]
        st.dataframe(
            view[[c for c in display_cols if c in view.columns]],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Sugestões detalhadas para revisão humana")
    if operational_actions is None:
        show_missing(
            "Sugestões operacionais v2.2",
            operational_dir / "operational_action_suggestions_v2_2.csv",
        )
    else:
        domains = ["Todos"] + sorted(
            operational_actions["domain"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )
        selected_domain = st.selectbox(
            "Filtrar domínio",
            domains,
            key="operational_action_domain_filter",
        )
        action_view = operational_actions.copy()
        if selected_domain != "Todos":
            action_view = action_view.loc[
                action_view["domain"].astype(str).eq(selected_domain)
            ]
        action_cols = [
            "codigo_ibge",
            "municipio",
            "domain",
            "title",
            "suggested_review_owner",
            "suggested_timeframe",
            "action_text",
            "signal_confidence",
            "evidence_summary",
            "suggestion_status",
            "human_review_required",
            "automatic_execution",
        ]
        st.dataframe(
            action_view[[c for c in action_cols if c in action_view.columns]],
            use_container_width=True,
            hide_index=True,
        )

    if domain_review_queues is not None and not domain_review_queues.empty:
        st.markdown("### Filas por domínio/responsável")
        st.dataframe(
            domain_review_queues,
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.2: revisão humana obrigatória, execução automática desabilitada, "
        "sem decisão em nível de paciente e sem score composto."
    )

with tabs[6]:
    st.subheader("Persistência das filas de revisão — v2.3")
    st.warning(
        "Persistência, entrada ou mudança de fila não representam gravidade ou risco. "
        "A v2.3 serve apenas para contextualizar a continuidade da revisão humana entre snapshots."
    )
    if operational_persistence is None:
        show_missing(
            "Persistência operacional v2.3",
            persistence_dir / "operational_persistence_v2_3.csv",
        )
    else:
        if "change_state" in operational_persistence.columns:
            counts = (
                operational_persistence["change_state"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("estado")
                .reset_index(name="municipios")
            )
            fig = px.bar(
                counts,
                x="estado",
                y="municipios",
                title="Mudanças entre vintages da fila operacional",
            )
            st.plotly_chart(fig, use_container_width=True)

        states = ["Todos"]
        if "change_state" in operational_persistence.columns:
            states += sorted(
                operational_persistence["change_state"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        selected_state = st.selectbox(
            "Filtrar estado de mudança",
            states,
            key="operational_persistence_filter",
        )
        view = operational_persistence.copy()
        if selected_state != "Todos":
            view = view.loc[
                view["change_state"].astype(str).eq(selected_state)
            ]

        cols = [
            "codigo_ibge",
            "municipio",
            "previous_review_queue",
            "review_queue",
            "change_state",
            "new_review_tags",
            "resolved_review_tags",
            "current_snapshot_id",
            "previous_snapshot_id",
            "change_state_is_not_risk",
            "persistence_is_not_severity",
            "automatic_action_enabled",
        ]
        st.dataframe(
            view[[c for c in cols if c in view.columns]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Governança v2.3: change_state_is_not_risk=true, "
            "persistence_is_not_severity=true e automatic_action_enabled=false."
        )

with tabs[7]:
    st.subheader("Estabilidade do workflow — v2.4")
    st.warning(
        "Estabilidade, persistência e churn descrevem o workflow entre vintages. "
        "Não representam risco, gravidade ou prioridade clínica."
    )
    if operational_stability is None:
        show_missing(
            "Estabilidade operacional v2.4",
            stability_dir / "operational_stability_v2_4.csv",
        )
    else:
        if "workflow_pattern" in operational_stability.columns:
            counts = (
                operational_stability["workflow_pattern"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("padrao")
                .reset_index(name="municipios")
            )
            fig = px.bar(
                counts,
                x="padrao",
                y="municipios",
                title="Padrões de estabilidade do workflow",
            )
            st.plotly_chart(fig, use_container_width=True)

        patterns = ["Todos"]
        if "workflow_pattern" in operational_stability.columns:
            patterns += sorted(
                operational_stability["workflow_pattern"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        selected_pattern = st.selectbox(
            "Filtrar padrão de workflow",
            patterns,
            key="operational_stability_filter",
        )
        view = operational_stability.copy()
        if selected_pattern != "Todos":
            view = view.loc[
                view["workflow_pattern"].astype(str).eq(selected_pattern)
            ]

        cols = [
            "codigo_ibge",
            "municipio",
            "current_review_queue",
            "workflow_pattern",
            "vintages_observed",
            "nonroutine_cycles",
            "current_nonroutine_run",
            "longest_nonroutine_run",
            "current_same_queue_run",
            "queue_change_count",
            "workflow_churn_rate",
            "single_cycle_reversion_count",
            "persistent_2plus_cycles",
            "sustained_3plus_cycles",
            "workflow_stability_is_not_risk",
            "persistence_is_not_severity",
            "automatic_action_enabled",
        ]
        st.dataframe(
            view[[c for c in cols if c in view.columns]],
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            "Governança v2.4: estabilidade não é risco; persistência não é gravidade; "
            "ação automática permanece desabilitada."
        )

with tabs[8]:
    st.subheader("Auditoria de decisão humana e follow-up — v2.5")
    st.warning(
        "A v2.5 registra decisões humanas e acompanhamento de workflow. "
        "Decisão registrada não é prova de execução externa, não é risco e não habilita ação automática."
    )

    c1, c2 = st.columns(2)
    with c1:
        if human_decisions_v25 is None:
            show_missing(
                "Decisões humanas validadas v2.5",
                decision_audit_dir / "human_decisions_validated_v2_5.csv",
            )
        else:
            st.metric("Decisões registradas", len(human_decisions_v25))
            if "decision_status" in human_decisions_v25.columns:
                counts = (
                    human_decisions_v25["decision_status"]
                    .astype("string")
                    .value_counts(dropna=False)
                    .rename_axis("decisao")
                    .reset_index(name="registros")
                )
                fig = px.bar(
                    counts,
                    x="decisao",
                    y="registros",
                    title="Decisões humanas registradas",
                )
                st.plotly_chart(fig, use_container_width=True)

    with c2:
        if follow_up_status_v25 is None:
            show_missing(
                "Estado de follow-up v2.5",
                decision_audit_dir / "follow_up_status_v2_5.csv",
            )
        else:
            if "follow_up_state" in follow_up_status_v25.columns:
                counts = (
                    follow_up_status_v25["follow_up_state"]
                    .astype("string")
                    .value_counts(dropna=False)
                    .rename_axis("estado")
                    .reset_index(name="registros")
                )
                fig = px.bar(
                    counts,
                    x="estado",
                    y="registros",
                    title="Estado dos follow-ups",
                )
                st.plotly_chart(fig, use_container_width=True)

    if human_decisions_v25 is not None:
        st.markdown("### Decisões humanas")
        decision_cols = [
            "decision_record_id",
            "codigo_ibge",
            "municipio",
            "snapshot_id",
            "review_queue",
            "decision_scope",
            "action_id",
            "reviewed_at",
            "reviewer_role",
            "decision_status",
            "rationale",
            "follow_up_required",
            "follow_up_due_at",
            "follow_up_owner_role",
            "decision_is_not_proof_of_execution",
            "automatic_execution_enabled",
        ]
        st.dataframe(
            human_decisions_v25[
                [c for c in decision_cols if c in human_decisions_v25.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    if follow_up_status_v25 is not None:
        st.markdown("### Follow-up")
        follow_cols = [
            "decision_record_id",
            "codigo_ibge",
            "municipio",
            "decision_status",
            "follow_up_required",
            "follow_up_due_at",
            "follow_up_owner_role",
            "latest_follow_up_event_status",
            "latest_follow_up_event_at",
            "follow_up_state",
            "as_of",
            "follow_up_state_is_not_risk",
            "automatic_execution_enabled",
        ]
        st.dataframe(
            follow_up_status_v25[
                [c for c in follow_cols if c in follow_up_status_v25.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    if follow_up_events_v25 is not None and not follow_up_events_v25.empty:
        with st.expander("Eventos de follow-up registrados"):
            st.dataframe(
                follow_up_events_v25,
                use_container_width=True,
                hide_index=True,
            )

    st.caption(
        "Governança v2.5: decisão humana registrada, execução automática desabilitada, "
        "sem decisão em nível de paciente e sem prescrição clínica."
    )

with tabs[9]:
    st.subheader("Concordância entre workflow e decisão humana — v2.6")
    st.warning(
        "A v2.6 serve para revisar regras do sistema. Discordância não significa erro humano, "
        "e concordância não prova correção epidemiológica da regra."
    )

    if workflow_concordance_v26 is None:
        show_missing(
            "Concordância workflow × decisão v2.6",
            concordance_dir / "human_workflow_concordance_v2_6.csv",
        )
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Decisões avaliadas", len(workflow_concordance_v26))
        with c2:
            if "rule_review_required" in workflow_concordance_v26.columns:
                review_required = (
                    workflow_concordance_v26["rule_review_required"]
                    .astype(str)
                    .str.lower()
                    .isin({"true", "1", "yes", "sim"})
                    .sum()
                )
                st.metric("Registros para revisão de regra", int(review_required))

        if "workflow_alignment" in workflow_concordance_v26.columns:
            counts = (
                workflow_concordance_v26["workflow_alignment"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("classe")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="classe",
                y="registros",
                title="Concordância entre fila e decisão humana",
            )
            st.plotly_chart(fig, use_container_width=True)

        alignment_options = ["Todas"]
        if "workflow_alignment" in workflow_concordance_v26.columns:
            alignment_options += sorted(
                workflow_concordance_v26["workflow_alignment"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        selected_alignment = st.selectbox(
            "Filtrar classe de concordância",
            alignment_options,
            key="workflow_concordance_v26_filter",
        )
        view = workflow_concordance_v26.copy()
        if selected_alignment != "Todas":
            view = view.loc[
                view["workflow_alignment"].astype(str).eq(selected_alignment)
            ]

        cols = [
            "decision_record_id",
            "codigo_ibge",
            "municipio",
            "snapshot_id",
            "review_queue",
            "decision_status",
            "workflow_alignment",
            "rule_review_required",
            "workflow_pattern",
            "current_nonroutine_run",
            "follow_up_state",
            "human_decision_is_epidemiological_gold_standard",
            "reviewer_score_enabled",
            "municipality_rank_enabled",
            "automatic_rule_change_enabled",
            "automatic_execution_enabled",
        ]
        st.dataframe(
            view[[c for c in cols if c in view.columns]],
            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Governança v2.6: sem score de revisor, sem ranking municipal, "
            "sem mudança automática de regra e sem execução automática."
        )

with tabs[10]:
    st.subheader("Propostas de mudança de regra — v2.7")
    st.warning(
        "Proposta não é mudança aplicada. Nenhuma regra ou threshold é alterado "
        "automaticamente; toda mudança exige análise e aprovação humana."
    )

    if rule_change_proposals is None:
        show_missing(
            "Propostas de mudança v2.7",
            proposal_dir / "rule_change_proposals_v2_7.csv",
        )
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Propostas", len(rule_change_proposals))
        with c2:
            if "affected_records" in rule_change_proposals.columns:
                st.metric(
                    "Registros afetados",
                    int(pd.to_numeric(
                        rule_change_proposals["affected_records"],
                        errors="coerce",
                    ).fillna(0).sum()),
                )

        if "proposal_type" in rule_change_proposals.columns:
            counts = (
                rule_change_proposals["proposal_type"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("tipo")
                .reset_index(name="propostas")
            )
            fig = px.bar(
                counts,
                x="tipo",
                y="propostas",
                title="Propostas por tipo",
            )
            st.plotly_chart(fig, use_container_width=True)

        display_cols = [
            "proposal_id",
            "rule_key",
            "workflow_alignment",
            "affected_records",
            "affected_municipalities",
            "proposal_type",
            "proposal_status",
            "problem_statement",
            "analysis_required",
            "automatic_rule_change_enabled",
            "automatic_threshold_change_enabled",
            "proposal_is_not_change",
            "human_approval_required",
        ]
        st.dataframe(
            rule_change_proposals[
                [c for c in display_cols if c in rule_change_proposals.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Avaliação em modo sombra")
    st.info(
        "O modo sombra compara fila atual e candidata sem ativar a regra candidata. "
        "Maior concordância com decisões humanas não equivale a maior acurácia epidemiológica."
    )

    if rule_shadow_evaluation_v27 is None:
        st.info(
            "Avaliação de regra candidata em modo sombra v2.7 ainda não disponível em "
            "data_candidate/rule_shadow_evaluation_v2_7/<proposal_id>/."
        )
    else:
        if rule_shadow_source_v27 is not None:
            st.caption(
                "Resultado shadow carregado de: "
                + str(rule_shadow_source_v27.relative_to(ROOT))
            )
        if "proposal_id" in rule_shadow_evaluation_v27.columns:
            proposal_values = sorted(
                rule_shadow_evaluation_v27["proposal_id"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
            if proposal_values:
                st.write("**Proposta em revisão:**", ", ".join(proposal_values))
        municipality_view = rule_shadow_evaluation_v27.drop_duplicates("codigo_ibge")
        c1, c2 = st.columns(2)
        with c1:
            st.metric(
                "Municípios avaliados",
                municipality_view["codigo_ibge"].nunique(),
            )
        with c2:
            if "queue_changed" in municipality_view.columns:
                changed = (
                    municipality_view["queue_changed"]
                    .astype(str)
                    .str.lower()
                    .isin({"true", "1", "yes", "sim"})
                    .sum()
                )
                st.metric("Municípios que mudariam de fila", int(changed))

        if "alignment_delta" in rule_shadow_evaluation_v27.columns:
            counts = (
                rule_shadow_evaluation_v27["alignment_delta"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("mudanca_concordancia")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="mudanca_concordancia",
                y="registros",
                title="Mudança de concordância do workflow no modo sombra",
            )
            st.plotly_chart(fig, use_container_width=True)

        shadow_cols = [
            "codigo_ibge",
            "municipio",
            "current_review_queue",
            "candidate_review_queue",
            "queue_changed",
            "queue_transition",
            "decision_record_id",
            "decision_status",
            "current_alignment",
            "candidate_alignment",
            "alignment_delta",
            "proposal_id",
            "candidate_rule_version",
            "shadow_only",
            "automatic_activation_enabled",
            "automatic_rule_change_enabled",
            "reviewer_score_enabled",
            "municipality_rank_enabled",
            "human_decision_is_epidemiological_gold_standard",
        ]
        st.dataframe(
            rule_shadow_evaluation_v27[
                [c for c in shadow_cols if c in rule_shadow_evaluation_v27.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.7: proposta ≠ mudança; alterações de lógica/threshold exigem "
        "revisão de casos, backtesting, revisão epidemiológica/estatística e aprovação humana."
    )

with tabs[11]:
    st.subheader("Avaliação formal de propostas — v2.8")
    st.warning(
        "Aprovação v2.8 autoriza apenas preparação de branch de implementação. "
        "Ela não altera regra, threshold, main ou produção automaticamente."
    )

    if rule_change_evaluations_v28 is None:
        show_missing(
            "Avaliações formais v2.8",
            evaluation_dir / "rule_change_evaluations_validated_v2_8.csv",
        )
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Avaliações", len(rule_change_evaluations_v28))
        with c2:
            if "final_decision" in rule_change_evaluations_v28.columns:
                approved = (
                    rule_change_evaluations_v28["final_decision"]
                    .astype(str)
                    .eq("approve_for_implementation_branch")
                    .sum()
                )
                st.metric("Aprovadas para branch", int(approved))
        with c3:
            if "final_decision" in rule_change_evaluations_v28.columns:
                deferred = (
                    rule_change_evaluations_v28["final_decision"]
                    .astype(str)
                    .eq("defer")
                    .sum()
                )
                st.metric("Adiadas", int(deferred))

        with c4:
            if "shadow_evidence_present" in rule_change_evaluations_v28.columns:
                shadow_count = (
                    rule_change_evaluations_v28["shadow_evidence_present"]
                    .astype(str)
                    .str.lower()
                    .isin({"true", "1", "yes", "sim"})
                    .sum()
                )
                st.metric("Com evidência shadow", int(shadow_count))

        if "final_decision" in rule_change_evaluations_v28.columns:
            counts = (
                rule_change_evaluations_v28["final_decision"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("decisao")
                .reset_index(name="avaliacoes")
            )
            fig = px.bar(
                counts,
                x="decisao",
                y="avaliacoes",
                title="Decisões formais sobre propostas",
            )
            st.plotly_chart(fig, use_container_width=True)

        display_cols = [
            "evaluation_record_id",
            "proposal_id",
            "proposal_type",
            "source_proposal_status",
            "evaluated_at",
            "reviewer_role",
            "case_review_status",
            "epidemiology_review_status",
            "shadow_review_status",
            "shadow_evidence_present",
            "shadow_candidate_rule_version",
            "shadow_queue_change_fraction",
            "shadow_review_is_not_activation",
            "backtest_status",
            "statistical_review_status",
            "documentation_status",
            "impact_summary",
            "risk_summary",
            "final_decision",
            "decision_rationale",
            "decision_is_not_implementation",
            "automatic_rule_change_enabled",
            "automatic_threshold_change_enabled",
            "automatic_merge_enabled",
            "automatic_deploy_enabled",
            "human_approval_required",
        ]
        st.dataframe(
            rule_change_evaluations_v28[
                [c for c in display_cols if c in rule_change_evaluations_v28.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.8: decisão ≠ implementação. Mudança lógica só pode ser aprovada "
        "com proposta elegível + evidência shadow v2.7 + backtest/revisões completos; "
        "merge/deploy automáticos permanecem desabilitados."
    )

with tabs[12]:
    st.subheader("Pacotes controlados de implementação — v2.9")
    st.warning(
        "Pacote v2.9 não é implementação. Ele apenas prepara uma branch manual, "
        "com arquivos-alvo, testes, critérios de aceitação e rollback."
    )

    if implementation_packages_v29 is None:
        show_missing(
            "Pacotes de implementação v2.9",
            implementation_dir / "implementation_packages_validated_v2_9.csv",
        )
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Pacotes", len(implementation_packages_v29))
        with c2:
            if "package_status" in implementation_packages_v29.columns:
                ready = (
                    implementation_packages_v29["package_status"]
                    .astype(str)
                    .eq("ready_for_manual_branch")
                    .sum()
                )
                st.metric("Prontos para branch manual", int(ready))

        display_cols = [
            "implementation_package_id",
            "proposal_id",
            "evaluation_record_id",
            "proposal_type",
            "rule_key",
            "created_at",
            "planner_role",
            "implementation_summary",
            "target_paths",
            "required_tests",
            "acceptance_criteria",
            "rollback_plan",
            "package_status",
            "target_branch_suggestion",
            "package_is_not_implementation",
            "manual_branch_required",
            "automatic_branch_creation_enabled",
            "automatic_code_edit_enabled",
            "automatic_commit_enabled",
            "automatic_merge_enabled",
            "automatic_deploy_enabled",
            "human_review_required",
        ]
        st.dataframe(
            implementation_packages_v29[
                [c for c in display_cols if c in implementation_packages_v29.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.9: branch manual obrigatória; criação de branch, edição, commit, "
        "merge e deploy automáticos permanecem desabilitados."
    )

with tabs[13]:
    st.subheader("Gate de implementação e merge — v2.10")
    st.warning(
        "Elegível para merge humano não significa merge executado. "
        "Commit, merge e deploy automáticos permanecem desabilitados."
    )

    if merge_gate_records_v210 is None:
        show_missing(
            "Gate de merge v2.10",
            merge_gate_dir / "merge_gate_validated_v2_10.csv",
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Registros", len(merge_gate_records_v210))
        with c2:
            if "final_gate_decision" in merge_gate_records_v210.columns:
                eligible = (
                    merge_gate_records_v210["final_gate_decision"]
                    .astype(str)
                    .eq("eligible_for_human_merge")
                    .sum()
                )
                st.metric("Elegíveis para merge humano", int(eligible))
        with c3:
            if "final_gate_decision" in merge_gate_records_v210.columns:
                blocked = (
                    merge_gate_records_v210["final_gate_decision"]
                    .astype(str)
                    .eq("blocked")
                    .sum()
                )
                st.metric("Bloqueados", int(blocked))

        if "final_gate_decision" in merge_gate_records_v210.columns:
            counts = (
                merge_gate_records_v210["final_gate_decision"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("decisao")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="decisao",
                y="registros",
                title="Decisões do gate v2.10",
            )
            st.plotly_chart(fig, use_container_width=True)

        display_cols = [
            "merge_gate_record_id",
            "implementation_package_id",
            "proposal_id",
            "proposal_type",
            "source_branch",
            "implementation_branch",
            "source_commit_sha",
            "implementation_commit_sha",
            "changed_paths",
            "authorized_target_paths",
            "diff_review_status",
            "scope_review_status",
            "ci_status",
            "regression_tests_status",
            "backtest_status",
            "epidemiology_revalidation_status",
            "statistical_revalidation_status",
            "security_privacy_review_status",
            "acceptance_criteria_status",
            "rollback_verification_status",
            "final_gate_decision",
            "gate_rationale",
            "merge_eligibility_is_not_merge",
            "automatic_commit_enabled",
            "automatic_merge_enabled",
            "automatic_deploy_enabled",
            "human_merge_required",
        ]
        st.dataframe(
            merge_gate_records_v210[
                [c for c in display_cols if c in merge_gate_records_v210.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.10: o gate apenas declara elegibilidade. "
        "Merge e deploy continuam sendo decisões e ações humanas separadas."
    )

with tabs[14]:
    st.subheader("Decisão humana de merge e pós-merge — v2.11")
    st.warning(
        "Aprovar merge não executa o merge. Registros pós-merge exigem evidência explícita "
        "do merge e não representam deploy automático."
    )

    if human_merge_decisions_v211 is None:
        show_missing(
            "Decisões humanas de merge v2.11",
            human_merge_dir / "human_merge_decisions_validated_v2_11.csv",
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Decisões", len(human_merge_decisions_v211))
        with c2:
            approved = (
                human_merge_decisions_v211["merge_decision"]
                .astype(str)
                .eq("approve_human_merge")
                .sum()
                if "merge_decision" in human_merge_decisions_v211.columns
                else 0
            )
            st.metric("Aprovações humanas", int(approved))
        with c3:
            deferred = (
                human_merge_decisions_v211["merge_decision"]
                .astype(str)
                .eq("defer_merge")
                .sum()
                if "merge_decision" in human_merge_decisions_v211.columns
                else 0
            )
            st.metric("Adiadas", int(deferred))

        decision_cols = [
            "merge_decision_record_id",
            "merge_gate_record_id",
            "implementation_package_id",
            "proposal_id",
            "implementation_branch",
            "implementation_commit_sha",
            "decided_at",
            "reviewer_role",
            "merge_decision",
            "decision_rationale",
            "merge_decision_is_not_merge_execution",
            "automatic_merge_enabled",
            "automatic_deploy_enabled",
            "automatic_rollback_enabled",
            "human_merge_required",
        ]
        st.dataframe(
            human_merge_decisions_v211[
                [c for c in decision_cols if c in human_merge_decisions_v211.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Verificação pós-merge")
    if post_merge_records_v211 is None:
        show_missing(
            "Registros pós-merge v2.11",
            human_merge_dir / "post_merge_records_validated_v2_11.csv",
        )
    else:
        if "post_merge_state" in post_merge_records_v211.columns:
            counts = (
                post_merge_records_v211["post_merge_state"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("estado")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="estado",
                y="registros",
                title="Estados pós-merge",
            )
            st.plotly_chart(fig, use_container_width=True)

        post_cols = [
            "post_merge_record_id",
            "merge_decision_record_id",
            "merge_gate_record_id",
            "implementation_package_id",
            "implementation_branch",
            "implementation_commit_sha",
            "merged_commit_sha",
            "merge_result_mode",
            "merge_evidence_ref",
            "recorded_at",
            "reviewer_role",
            "post_merge_ci_status",
            "smoke_test_status",
            "epidemiology_sanity_status",
            "security_privacy_check_status",
            "rollback_readiness_status",
            "post_merge_state",
            "verification_notes",
            "post_merge_record_requires_actual_merge_evidence",
            "post_merge_record_is_not_deploy",
            "automatic_deploy_enabled",
            "automatic_rollback_enabled",
        ]
        st.dataframe(
            post_merge_records_v211[
                [c for c in post_cols if c in post_merge_records_v211.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.11: decisão de merge ≠ execução; pós-merge exige evidência real; "
        "deploy e rollback automáticos permanecem desabilitados."
    )

with tabs[15]:
    st.subheader("Release gate, deploy humano e verificação de efeito — v2.12")
    st.warning(
        "Elegibilidade não é deploy. A decisão humana exige release gate aprovado; "
        "o deploy real deve usar exatamente o commit e ambiente autorizados, e a "
        "verificação de efeito não é inferência causal epidemiológica."
    )

    st.markdown("### Gate pré-deploy")
    if release_gate_records_v212 is None:
        show_missing(
            "Release gate v2.12",
            release_gate_dir / "release_deploy_gate_validated_v2_12.csv",
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Release gates", len(release_gate_records_v212))
        with c2:
            eligible = (
                release_gate_records_v212["final_release_decision"]
                .astype(str)
                .eq("eligible_for_human_deploy")
                .sum()
                if "final_release_decision" in release_gate_records_v212.columns
                else 0
            )
            st.metric("Elegíveis para decisão humana", int(eligible))
        with c3:
            blocked = (
                release_gate_records_v212["final_release_decision"]
                .astype(str)
                .eq("blocked")
                .sum()
                if "final_release_decision" in release_gate_records_v212.columns
                else 0
            )
            st.metric("Bloqueados", int(blocked))

        gate_cols = [
            "release_gate_record_id",
            "post_merge_record_id",
            "implementation_package_id",
            "target_environment",
            "verified_merged_commit_sha",
            "release_commit_sha",
            "release_version",
            "predeploy_ci_status",
            "predeploy_security_privacy_status",
            "monitoring_readiness_status",
            "rollback_plan_verification_status",
            "change_window_status",
            "final_release_decision",
            "release_rationale",
            "deploy_eligibility_is_not_deploy",
            "automatic_deploy_enabled",
            "automatic_rollback_enabled",
            "human_deploy_required",
        ]
        st.dataframe(
            release_gate_records_v212[
                [c for c in gate_cols if c in release_gate_records_v212.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Decisão humana de deploy")
    if human_deploy_decisions_v212 is None:
        show_missing(
            "Decisões humanas de deploy v2.12",
            deployment_dir / "human_deploy_decisions_validated_v2_12.csv",
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Decisões de deploy", len(human_deploy_decisions_v212))
        with c2:
            approved = (
                human_deploy_decisions_v212["deploy_decision"]
                .astype(str)
                .eq("approve_human_deploy")
                .sum()
                if "deploy_decision" in human_deploy_decisions_v212.columns
                else 0
            )
            st.metric("Aprovações humanas", int(approved))
        with c3:
            deferred = (
                human_deploy_decisions_v212["deploy_decision"]
                .astype(str)
                .eq("defer_deploy")
                .sum()
                if "deploy_decision" in human_deploy_decisions_v212.columns
                else 0
            )
            st.metric("Adiadas", int(deferred))

        deploy_decision_cols = [
            "deploy_decision_record_id",
            "release_gate_record_id",
            "post_merge_record_id",
            "implementation_package_id",
            "target_environment",
            "release_commit_sha",
            "merged_commit_sha",
            "decided_at",
            "reviewer_role",
            "deploy_decision",
            "decision_rationale",
            "deploy_decision_is_not_deploy_execution",
            "automatic_deploy_enabled",
            "automatic_rollback_enabled",
            "human_deploy_required",
        ]
        st.dataframe(
            human_deploy_decisions_v212[
                [c for c in deploy_decision_cols if c in human_deploy_decisions_v212.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Registro de deploy")
    if deployment_records_v212 is None:
        show_missing(
            "Registros de deploy v2.12",
            deployment_dir / "deployment_records_validated_v2_12.csv",
        )
    else:
        if "deployment_state" in deployment_records_v212.columns:
            counts = (
                deployment_records_v212["deployment_state"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("estado")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="estado",
                y="registros",
                title="Estados de deploy",
            )
            st.plotly_chart(fig, use_container_width=True)

        deployment_cols = [
            "deployment_record_id",
            "deploy_decision_record_id",
            "release_gate_record_id",
            "implementation_package_id",
            "environment",
            "release_commit_sha",
            "merged_commit_sha",
            "deployed_commit_sha",
            "deployed_at",
            "reviewer_role",
            "deploy_evidence_ref",
            "post_deploy_ci_status",
            "smoke_test_status",
            "health_check_status",
            "security_privacy_check_status",
            "rollback_readiness_status",
            "deployment_state",
            "deployment_notes",
            "automatic_deploy_enabled",
            "automatic_rollback_enabled",
            "deployment_is_not_effect_verification",
        ]
        st.dataframe(
            deployment_records_v212[
                [c for c in deployment_cols if c in deployment_records_v212.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Verificação pós-deploy")
    if effect_verification_v212 is None:
        show_missing(
            "Verificação de efeito v2.12",
            deployment_dir / "effect_verification_validated_v2_12.csv",
        )
    else:
        if "effect_state" in effect_verification_v212.columns:
            counts = (
                effect_verification_v212["effect_state"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("estado")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="estado",
                y="registros",
                title="Estados da verificação de efeito",
            )
            st.plotly_chart(fig, use_container_width=True)

        effect_cols = [
            "effect_verification_record_id",
            "deployment_record_id",
            "implementation_package_id",
            "deployed_commit_sha",
            "measured_at",
            "reviewer_role",
            "observation_window_start",
            "observation_window_end",
            "effect_state",
            "expected_behavior_summary",
            "observed_behavior_summary",
            "evidence_refs",
            "effect_review_notes",
            "effect_verification_is_not_causal_inference",
            "automatic_rule_change_enabled",
            "automatic_rollback_enabled",
        ]
        st.dataframe(
            effect_verification_v212[
                [c for c in effect_cols if c in effect_verification_v212.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.12: release gate obrigatório; decisão de deploy ≠ execução; "
        "commit e ambiente do deploy devem ser exatamente os autorizados; deploy exige evidência; "
        "verificação de efeito não é inferência causal; rollback e alteração de regra automáticos permanecem desabilitados."
    )

with tabs[16]:
    st.subheader("Rollback humano e verificação pós-rollback — v2.13")
    st.warning(
        "Rollback é sempre decisão e execução humana separadas. "
        "O sistema não executa rollback automaticamente e exige evidência explícita."
    )

    if rollback_decisions_v213 is None:
        show_missing(
            "Decisões de rollback v2.13",
            rollback_dir / "human_rollback_decisions_validated_v2_13.csv",
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Decisões de rollback", len(rollback_decisions_v213))
        with c2:
            approved = (
                rollback_decisions_v213["rollback_decision"]
                .astype(str)
                .eq("approve_human_rollback")
                .sum()
                if "rollback_decision" in rollback_decisions_v213.columns
                else 0
            )
            st.metric("Aprovações humanas", int(approved))
        with c3:
            deferred = (
                rollback_decisions_v213["rollback_decision"]
                .astype(str)
                .eq("defer_rollback")
                .sum()
                if "rollback_decision" in rollback_decisions_v213.columns
                else 0
            )
            st.metric("Adiadas", int(deferred))

        decision_cols = [
            "rollback_decision_record_id",
            "source_record_type",
            "source_record_id",
            "implementation_package_id",
            "deployed_commit_sha",
            "source_state",
            "rollback_target_commit_sha",
            "rollback_plan_ref",
            "decided_at",
            "reviewer_role",
            "rollback_decision",
            "decision_rationale",
            "rollback_decision_is_not_rollback_execution",
            "automatic_rollback_enabled",
            "automatic_rule_change_enabled",
        ]
        st.dataframe(
            rollback_decisions_v213[
                [c for c in decision_cols if c in rollback_decisions_v213.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Execução e verificação pós-rollback")
    if rollback_execution_v213 is None:
        show_missing(
            "Execução de rollback v2.13",
            rollback_dir / "rollback_execution_validated_v2_13.csv",
        )
    else:
        if "rollback_execution_state" in rollback_execution_v213.columns:
            counts = (
                rollback_execution_v213["rollback_execution_state"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("estado")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="estado",
                y="registros",
                title="Estados pós-rollback",
            )
            st.plotly_chart(fig, use_container_width=True)

        execution_cols = [
            "rollback_execution_record_id",
            "rollback_decision_record_id",
            "implementation_package_id",
            "rollback_target_commit_sha",
            "rolled_back_commit_sha",
            "rolled_back_at",
            "reviewer_role",
            "rollback_evidence_ref",
            "post_rollback_ci_status",
            "smoke_test_status",
            "health_check_status",
            "security_privacy_check_status",
            "epidemiology_sanity_status",
            "rollback_execution_state",
            "verification_notes",
            "rollback_record_requires_actual_rollback_evidence",
            "automatic_rollback_enabled",
            "automatic_rule_change_enabled",
        ]
        st.dataframe(
            rollback_execution_v213[
                [c for c in execution_cols if c in rollback_execution_v213.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.13: decisão de rollback ≠ execução; rollback exige evidência real; "
        "alteração de regra, deploy e rollback automáticos permanecem desabilitados."
    )

with tabs[17]:
    st.subheader("Post-mortem e aprendizado controlado — v2.14")
    st.warning(
        "Aprendizado institucional não é prova causal e não altera regras automaticamente. "
        "O retorno ao ciclo de regra exige revisão humana explícita."
    )

    if postmortem_records_v214 is None:
        show_missing(
            "Post-mortem v2.14",
            postmortem_dir / "postmortem_validated_v2_14.csv",
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Post-mortems", len(postmortem_records_v214))
        with c2:
            closed = (
                postmortem_records_v214["postmortem_status"]
                .astype(str)
                .eq("closed")
                .sum()
                if "postmortem_status" in postmortem_records_v214.columns
                else 0
            )
            st.metric("Fechados", int(closed))
        with c3:
            reentries = (
                postmortem_records_v214["reenter_rule_review"]
                .astype(str)
                .str.lower()
                .isin({"true", "1", "yes", "sim"})
                .sum()
                if "reenter_rule_review" in postmortem_records_v214.columns
                else 0
            )
            st.metric("Retornos à revisão de regra", int(reentries))

        if "outcome_state" in postmortem_records_v214.columns:
            counts = (
                postmortem_records_v214["outcome_state"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("desfecho")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="desfecho",
                y="registros",
                title="Desfechos dos post-mortems",
            )
            st.plotly_chart(fig, use_container_width=True)

        if "learning_action_type" in postmortem_records_v214.columns:
            counts = (
                postmortem_records_v214["learning_action_type"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("acao")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="acao",
                y="registros",
                title="Ações de aprendizado",
            )
            st.plotly_chart(fig, use_container_width=True)

        display_cols = [
            "postmortem_record_id",
            "source_record_type",
            "source_record_id",
            "implementation_package_id",
            "source_state",
            "technical_commit_sha",
            "conducted_at",
            "reviewer_role",
            "postmortem_status",
            "outcome_state",
            "event_summary",
            "expected_behavior_summary",
            "observed_behavior_summary",
            "contributing_factors",
            "safeguards_that_worked",
            "safeguards_to_improve",
            "lessons_learned",
            "learning_action_type",
            "follow_up_actions",
            "evidence_refs",
            "reenter_rule_review",
            "rule_review_scope",
            "rule_review_reason",
            "postmortem_is_not_causal_proof",
            "learning_is_not_rule_change",
            "rule_reentry_requires_human_review",
            "automatic_rule_change_enabled",
            "automatic_issue_creation_enabled",
        ]
        st.dataframe(
            postmortem_records_v214[
                [c for c in display_cols if c in postmortem_records_v214.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.14: lição ≠ mudança aplicada; fatores contribuintes ≠ prova causal; "
        "qualquer retorno ao ciclo de regra depende de revisão humana."
    )

with tabs[18]:
    st.subheader("Ledger auditável do ciclo de mudança — v2.15")
    st.warning(
        "O ledger é observacional: valida linhagem, cronologia, commit e ambiente. "
        "Ele não executa mudanças, deploys, rollbacks ou qualquer ação automática."
    )

    if change_lifecycle_v215 is None:
        show_missing(
            "Ledger do ciclo de mudança v2.15",
            ledger_dir / "change_lifecycle_ledger_v2_15.csv",
        )
    else:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Eventos", len(change_lifecycle_v215))
        with c2:
            proposals = (
                change_lifecycle_v215["proposal_id"].nunique()
                if "proposal_id" in change_lifecycle_v215.columns
                else 0
            )
            st.metric("Propostas com linhagem", int(proposals))
        with c3:
            valid = (
                change_lifecycle_v215["lineage_status"]
                .astype(str)
                .eq("linked_and_validated")
                .sum()
                if "lineage_status" in change_lifecycle_v215.columns
                else 0
            )
            st.metric("Eventos validados", int(valid))

        if "event_type" in change_lifecycle_v215.columns:
            counts = (
                change_lifecycle_v215["event_type"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("evento")
                .reset_index(name="registros")
            )
            fig = px.bar(
                counts,
                x="evento",
                y="registros",
                title="Eventos por estágio do ciclo de mudança",
            )
            st.plotly_chart(fig, use_container_width=True)

        proposal_options = ["Todas"]
        if "proposal_id" in change_lifecycle_v215.columns:
            proposal_options += sorted(
                change_lifecycle_v215["proposal_id"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )
        selected_proposal = st.selectbox(
            "Filtrar proposta",
            proposal_options,
            key="change_lifecycle_proposal_filter_v215",
        )
        view = change_lifecycle_v215.copy()
        if selected_proposal != "Todas":
            view = view.loc[
                view["proposal_id"].astype(str).eq(selected_proposal)
            ]

        display_cols = [
            "event_key",
            "stage_order",
            "event_type",
            "record_id",
            "parent_event_key",
            "event_at",
            "state",
            "proposal_id",
            "implementation_package_id",
            "commit_sha",
            "environment",
            "lineage_status",
            "ledger_is_not_execution",
            "ledger_does_not_trigger_actions",
            "automatic_action_enabled",
            "human_review_required",
        ]
        st.dataframe(
            view[[c for c in display_cols if c in view.columns]],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.15: cadeia de custódia técnica somente. "
        "Eventos órfãos, transições impossíveis, regressão cronológica, quebra de commit "
        "ou ambiente inconsistente devem bloquear a construção do ledger."
    )

with tabs[19]:
    st.subheader("Observabilidade do processo de governança — v2.16")
    st.warning(
        "Estas métricas descrevem fluxo e tempo de processo. Não são score de pessoas, "
        "não ranqueiam municípios, não representam risco epidemiológico e os thresholds "
        "experimentais não são SLA institucional."
    )

    if governance_status_v216 is None:
        show_missing(
            "Status de governança v2.16",
            governance_observability_dir / "governance_proposal_status_v2_16.csv",
        )
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Propostas", len(governance_status_v216))
        with c2:
            open_count = (
                (~governance_status_v216["terminal_stage"]
                 .astype(str).str.lower()
                 .isin({"true", "1", "yes", "sim"}))
                .sum()
                if "terminal_stage" in governance_status_v216.columns
                else 0
            )
            st.metric("Em fluxo", int(open_count))
        with c3:
            stale_count = (
                governance_status_v216["stale_experimental"]
                .astype(str)
                .str.lower()
                .isin({"true", "1", "yes", "sim"})
                .sum()
                if "stale_experimental" in governance_status_v216.columns
                else 0
            )
            st.metric("Flags experimentais", int(stale_count))
        with c4:
            terminal_count = (
                governance_status_v216["terminal_stage"]
                .astype(str)
                .str.lower()
                .isin({"true", "1", "yes", "sim"})
                .sum()
                if "terminal_stage" in governance_status_v216.columns
                else 0
            )
            st.metric("Estágio terminal", int(terminal_count))

        if "current_stage" in governance_status_v216.columns:
            counts = (
                governance_status_v216["current_stage"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("estagio")
                .reset_index(name="propostas")
            )
            fig = px.bar(
                counts,
                x="estagio",
                y="propostas",
                title="Propostas por estágio atual",
            )
            st.plotly_chart(fig, use_container_width=True)

        status_cols = [
            "proposal_id",
            "current_stage",
            "current_state",
            "events_count",
            "first_event_at",
            "last_event_at",
            "hours_since_last_event",
            "total_observed_hours",
            "stale_threshold_hours",
            "stale_experimental",
            "terminal_stage",
            "deployment_seen",
            "effect_verification_seen",
            "rollback_decision_seen",
            "rollback_execution_seen",
            "threshold_status",
            "stale_flag_is_not_risk",
            "reviewer_score_enabled",
            "municipality_rank_enabled",
            "automatic_action_enabled",
            "as_of",
        ]
        st.dataframe(
            governance_status_v216[
                [c for c in status_cols if c in governance_status_v216.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("### Tempos entre etapas")
    if governance_transitions_v216 is None:
        show_missing(
            "Métricas de transição v2.16",
            governance_observability_dir / "governance_transition_metrics_v2_16.csv",
        )
    else:
        computed = governance_transitions_v216.copy()
        if {
            "duration_status",
            "transition_hours",
            "event_type",
        }.issubset(computed.columns):
            computed = computed.loc[
                computed["duration_status"].astype(str).eq("computed")
            ].copy()
            computed["transition_hours"] = pd.to_numeric(
                computed["transition_hours"],
                errors="coerce",
            )
            stage_medians = (
                computed.groupby("event_type", as_index=False)["transition_hours"]
                .median()
                .dropna()
            )
            if not stage_medians.empty:
                fig = px.bar(
                    stage_medians,
                    x="event_type",
                    y="transition_hours",
                    title="Mediana observada até cada etapa (horas)",
                )
                st.plotly_chart(fig, use_container_width=True)

        transition_cols = [
            "proposal_id",
            "parent_event_type",
            "event_type",
            "transition_hours",
            "duration_status",
            "process_metric_is_not_performance_score",
            "reviewer_score_enabled",
            "municipality_rank_enabled",
        ]
        st.dataframe(
            governance_transitions_v216[
                [c for c in transition_cols if c in governance_transitions_v216.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.16: thresholds = experimental_internal_not_sla; "
        "stale ≠ risco; métricas de processo ≠ avaliação de desempenho; "
        "nenhuma flag dispara ação automaticamente."
    )


with tabs[20]:
    st.subheader("Follow-up auditável das ações de aprendizado — v2.17")
    st.warning(
        "Conclusão de ação não é prova de efetividade epidemiológica. "
        "Fechamento verificado exige evidência e revisão humana; overdue é atraso de workflow, não risco."
    )

    if learning_action_followup_v217 is None:
        show_missing(
            "Follow-up de aprendizado v2.17",
            learning_action_followup_dir / "learning_action_followup_validated_v2_17.csv",
        )
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Ações", len(learning_action_followup_v217))
        with c2:
            overdue = (
                learning_action_followup_v217["overdue"]
                .astype(str)
                .str.lower()
                .isin({"true", "1", "yes", "sim"})
                .sum()
                if "overdue" in learning_action_followup_v217.columns
                else 0
            )
            st.metric("Atrasadas", int(overdue))
        with c3:
            verified = (
                learning_action_followup_v217["follow_up_state"]
                .astype(str)
                .eq("verified_closed")
                .sum()
                if "follow_up_state" in learning_action_followup_v217.columns
                else 0
            )
            st.metric("Fechadas e verificadas", int(verified))
        with c4:
            blocked = (
                learning_action_followup_v217["follow_up_state"]
                .astype(str)
                .isin({"blocked", "blocked_overdue"})
                .sum()
                if "follow_up_state" in learning_action_followup_v217.columns
                else 0
            )
            st.metric("Bloqueadas", int(blocked))

        if "follow_up_state" in learning_action_followup_v217.columns:
            counts = (
                learning_action_followup_v217["follow_up_state"]
                .astype("string")
                .value_counts(dropna=False)
                .rename_axis("estado")
                .reset_index(name="acoes")
            )
            fig = px.bar(
                counts,
                x="estado",
                y="acoes",
                title="Estados do follow-up das ações de aprendizado",
            )
            st.plotly_chart(fig, use_container_width=True)

        display_cols = [
            "learning_action_record_id",
            "postmortem_record_id",
            "implementation_package_id",
            "learning_action_type",
            "action_sequence",
            "action_description",
            "owner_role",
            "created_at",
            "due_at",
            "action_status",
            "status_updated_at",
            "completed_at",
            "completion_evidence_refs",
            "verification_status",
            "verified_at",
            "verifier_role",
            "verification_notes",
            "blocking_reason",
            "cancellation_rationale",
            "governance_handoff_ref",
            "follow_up_state",
            "overdue",
            "completion_is_not_effectiveness_proof",
            "verification_is_not_epidemiological_effect",
            "overdue_is_not_risk",
            "automatic_execution_enabled",
            "automatic_issue_creation_enabled",
            "automatic_rule_change_enabled",
        ]
        st.dataframe(
            learning_action_followup_v217[
                [c for c in display_cols if c in learning_action_followup_v217.columns]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "Governança v2.17: tracking ≠ execução; completed ≠ efetividade; "
        "verified_closed ≠ efeito causal; overdue ≠ risco; rule_review concluída exige handoff humano; "
        "execução, criação de issue e alteração de regra automáticas permanecem desabilitadas."
    )

st.divider()
st.caption(
    "Regra de governança: nenhum elemento desta tela altera publication_status, "
    "gera score composto ou ativa alerta operacional."
)
