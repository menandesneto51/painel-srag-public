# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / "data_candidate"

st.set_page_config(
    page_title="SRAG MT v2.4 — Revisão Local",
    layout="wide",
)

st.title("SRAG MT v2.4 — Revisão Local")
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

tabs = st.tabs([
    "Inteligência territorial",
    "Sinais",
    "Confiança e silêncio",
    "Virologia",
    "Backtesting",
    "Revisão operacional v2.2",
    "Persistência v2.3",
    "Estabilidade v2.4",
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

st.divider()
st.caption(
    "Regra de governança: nenhum elemento desta tela altera publication_status, "
    "gera score composto ou ativa alerta operacional."
)
