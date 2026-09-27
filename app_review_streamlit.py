# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
CANDIDATE = ROOT / "data_candidate"

st.set_page_config(
    page_title="SRAG MT v2.1 — Revisão Local",
    layout="wide",
)

st.title("SRAG MT v2.1 — Revisão Local")
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
operational_dir = CANDIDATE / "operational_review"

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
operational_queue = read_csv(operational_dir / "operational_review_queue_v2_2.csv")

tabs = st.tabs([
    "Inteligência territorial",
    "Sinais",
    "Confiança e silêncio",
    "Virologia",
    "Backtesting",
    "Revisão operacional v2.2",
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
    st.subheader("Fila de revisão operacional v2.2")
    st.warning(
        "A fila organiza o tipo de revisão técnica. Ela não é ranking de risco, "
        "não representa gravidade clínica e não executa ações automaticamente."
    )
    if operational_queue is None:
        show_missing(
            "Fila operacional v2.2",
            operational_dir / "operational_review_queue_v2_2.csv",
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
            "Filtrar fila de revisão",
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

        st.caption(
            "Governança v2.2: human_review_required=true, "
            "automatic_execution_enabled=false e queue_is_not_risk_rank=true."
        )

st.divider()
st.caption(
    "Regra de governança: nenhum elemento desta tela altera publication_status, "
    "gera score composto ou ativa alerta operacional."
)
