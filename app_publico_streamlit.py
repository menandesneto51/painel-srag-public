# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data_public"

st.set_page_config(page_title="Painel SRAG Público", layout="wide")

BLACK_LAYOUT = dict(
    font=dict(color="black"),
    title_font=dict(color="black"),
    xaxis=dict(title_font=dict(color="black"), tickfont=dict(color="black")),
    yaxis=dict(title_font=dict(color="black"), tickfont=dict(color="black")),
    legend=dict(font=dict(color="black")),
    paper_bgcolor="white",
    plot_bgcolor="white",
)

FILE_NAMES = {
    "kpis": "kpis.json",
    "weekly": "weekly_summary.csv",
    "risk": "risk_summary.csv",
    "silent": "silent_summary.csv",
    "virology": "virology_summary.csv",
    "forecast": "forecast_summary.csv",
    "or_obito": "or_obito_summary.csv",
    "or_uti": "or_uti_summary.csv",
    "metadata": "metadata_public.json",
}

def resolve_path(filename: str) -> Path:
    p1 = DATA_DIR / filename
    p2 = APP_DIR / filename
    if p1.exists():
        return p1
    if p2.exists():
        return p2
    return p1

def build_required_files():
    return {key: resolve_path(name) for key, name in FILE_NAMES.items()}

def check_files(required_files):
    return [str(p.name) for p in required_files.values() if not p.exists()]

@st.cache_data(show_spinner=False)
def load_public_data():
    required_files = build_required_files()

    kpis = json.loads(required_files["kpis"].read_text(encoding="utf-8"))
    metadata = json.loads(required_files["metadata"].read_text(encoding="utf-8"))

    weekly = pd.read_csv(required_files["weekly"])
    risk = pd.read_csv(required_files["risk"])
    silent = pd.read_csv(required_files["silent"])
    virology = pd.read_csv(required_files["virology"])
    forecast = pd.read_csv(required_files["forecast"])
    or_obito = pd.read_csv(required_files["or_obito"])
    or_uti = pd.read_csv(required_files["or_uti"])
    return required_files, kpis, metadata, weekly, risk, silent, virology, forecast, or_obito, or_uti

def fmt_value(val, is_percent=False):
    if pd.isna(val):
        return "NA"
    if is_percent:
        return f"{float(val):.1f}%"
    return f"{int(round(float(val))):,}".replace(",", ".")

def metric_card(label, total, ref_week=None, ref_value=None, delta_pct=None, is_percent=False):
    val = fmt_value(total, is_percent=is_percent)
    delta_txt = None if pd.isna(delta_pct) else f"{float(delta_pct):+.1f}%"
    st.metric(label, value=val, delta=delta_txt)
    if ref_week is not None and ref_value is not None and not pd.isna(ref_week):
        st.caption(f"SE ref. {int(ref_week)}: {fmt_value(ref_value, is_percent=is_percent)}")

def line_chart(df, x, y, title, color=None):
    fig = px.line(df, x=x, y=y, color=color, markers=True, title=title)
    fig.update_layout(**BLACK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

def bar_chart(df, x, y, title, color=None, orientation="v"):
    fig = px.bar(df, x=x, y=y, color=color, title=title, orientation=orientation)
    fig.update_layout(**BLACK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)

def main():
    required_files = build_required_files()
    missing = check_files(required_files)
    if missing:
        st.error("Arquivos públicos ausentes: " + ", ".join(missing))
        st.info("O app procura primeiro em data_public/ e depois na raiz do repositório.")
        st.stop()

    required_files, kpis, metadata, weekly, risk, silent, virology, forecast, or_obito, or_uti = load_public_data()

    st.title("Painel SRAG Público")
    st.caption("Versão publicável do painel: lê apenas agregados públicos, sem base bruta do SIVEP.")
    st.caption("Arquivos detectados automaticamente em data_public/ ou na raiz do repositório.")

    c1, c2, c3 = st.columns(3)
    c1.write(f"**Ano de referência:** {metadata.get('year', 'NA')}")
    c2.write(f"**SE estabilizada:** {metadata.get('stable_week', 'NA')}")
    c3.write(f"**Atualizado em:** {metadata.get('generated_at', 'NA')}")

    st.divider()

    weekly_ref = kpis.get("weekly_reference", {})
    weekly_prev = kpis.get("weekly_previous", {})

    labels = [
        ("Notificações", "notificacoes", False),
        ("Casos", "casos", False),
        ("Hospitalizações", "hospitalizacoes", False),
        ("Enfermaria", "enfermaria", False),
        ("UTI", "uti", False),
        ("Óbitos", "obitos", False),
        ("Curas", "cura", False),
        ("UTI/Hospitalizados", "taxa_uti_hosp_percent", True),
        ("Envio laboratorial", "taxa_envio_lab_percent", True),
    ]

    cols = st.columns(3)
    for i, (lab, key, is_pct) in enumerate(labels):
        with cols[i % 3]:
            ref_val = weekly_ref.get(key)
            prev_val = weekly_prev.get(key)
            delta = None
            if ref_val not in [None, ""] and prev_val not in [None, "", 0]:
                try:
                    prev = float(prev_val)
                    curr = float(ref_val)
                    if prev != 0:
                        delta = (curr / prev - 1.0) * 100.0
                except Exception:
                    delta = None
            metric_card(
                lab,
                kpis.get(key),
                ref_week=weekly_ref.get("SE_NOTIF"),
                ref_value=ref_val,
                delta_pct=delta,
                is_percent=is_pct,
            )

    st.divider()

    tabs = st.tabs([
        "Resumo",
        "Risco e Silêncio",
        "Virologia",
        "Nowcasting e Forecast",
        "Odds Ratio",
        "Arquivos"
    ])

    with tabs[0]:
        st.subheader("Resumo temporal")
        if not weekly.empty:
            line_chart(weekly, "SEMANA_NOTIF_INICIO", "notificacoes", "Notificações semanais")
            cc = st.columns(2)
            with cc[0]:
                line_chart(weekly, "SEMANA_NOTIF_INICIO", "uti", "UTI por semana")
            with cc[1]:
                line_chart(weekly, "SEMANA_NOTIF_INICIO", "obitos", "Óbitos por semana")
        else:
            st.info("Sem dados semanais.")

    with tabs[1]:
        st.subheader("Risco e municípios silenciosos")
        if not risk.empty:
            risk_view = risk.copy().sort_values("score_risco_srag", ascending=False)
            bar_chart(risk_view.head(20), "NM_MUN", "score_risco_srag", "Top 20 municípios por score de risco")
            st.dataframe(risk_view.head(30), use_container_width=True)
        else:
            st.info("Sem dados de risco.")
        st.markdown("**Municípios silenciosos prioritários**")
        if not silent.empty:
            st.dataframe(silent.head(30), use_container_width=True)
        else:
            st.info("Sem municípios silenciosos.")

    with tabs[2]:
        st.subheader("Virologia")
        if not virology.empty:
            identified = virology[~virology["virus"].astype("string").str.contains("Não identificado", case=False, na=False)]
            bar_chart(identified.head(15), "virus", "casos", "Vírus identificados")
            st.dataframe(virology, use_container_width=True)
        else:
            st.info("Sem resumo virológico.")

    with tabs[3]:
        st.subheader("Nowcasting e forecasting")
        if not forecast.empty:
            sub = forecast[forecast["metrica"] == "notificacoes"].copy()
            if not sub.empty:
                bar_chart(sub, "horizonte_dias", "valor_esperado", "Forecast de notificações (7, 15 e 30 dias)")
            st.dataframe(forecast, use_container_width=True)
        else:
            st.info("Sem forecast público.")

    with tabs[4]:
        st.subheader("Odds Ratio")
        cc = st.columns(2)
        with cc[0]:
            st.markdown("**Odds Ratio para óbito**")
            st.dataframe(or_obito, use_container_width=True)
        with cc[1]:
            st.markdown("**Odds Ratio para UTI**")
            st.dataframe(or_uti, use_container_width=True)

    with tabs[5]:
        st.subheader("Arquivos públicos localizados")
        for key, p in required_files.items():
            st.write(f"- {key}: {p}")

if __name__ == "__main__":
    main()
