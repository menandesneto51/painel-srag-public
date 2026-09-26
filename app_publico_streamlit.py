# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from public_data_validation import has_errors, validate_loaded_data, weekly_value

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
    "risk_candidate": "risk_summary_v2_candidate.csv",
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

    kpis = json.loads(required_files["kpis"].read_text(encoding="utf-8-sig"))
    metadata = json.loads(required_files["metadata"].read_text(encoding="utf-8-sig"))

    weekly = pd.read_csv(required_files["weekly"], encoding="utf-8-sig")
    risk = pd.read_csv(required_files["risk"], encoding="utf-8-sig")
    risk_candidate = pd.read_csv(required_files["risk_candidate"], encoding="utf-8-sig")
    silent = pd.read_csv(required_files["silent"], encoding="utf-8-sig")
    virology = pd.read_csv(required_files["virology"], encoding="utf-8-sig")
    forecast = pd.read_csv(required_files["forecast"], encoding="utf-8-sig")
    or_obito = pd.read_csv(required_files["or_obito"], encoding="utf-8-sig")
    or_uti = pd.read_csv(required_files["or_uti"], encoding="utf-8-sig")
    return required_files, kpis, metadata, weekly, risk, risk_candidate, silent, virology, forecast, or_obito, or_uti


def fmt_value(val, is_percent=False):
    if val is None or pd.isna(val):
        return "NA"
    if is_percent:
        return f"{float(val):.1f}%"
    return f"{int(round(float(val))):,}".replace(",", ".")


def metric_card(
    label,
    total,
    ref_week=None,
    ref_value=None,
    prev_week=None,
    prev_value=None,
    is_percent=False,
):
    st.metric(label, value=fmt_value(total, is_percent=is_percent))

    if ref_week is None or ref_value is None or pd.isna(ref_value):
        return

    caption = f"SE {int(ref_week)}: {fmt_value(ref_value, is_percent=is_percent)}"
    if prev_week is not None and prev_value is not None and not pd.isna(prev_value):
        caption += f" | SE {int(prev_week)}: {fmt_value(prev_value, is_percent=is_percent)}"
        try:
            prev = float(prev_value)
            curr = float(ref_value)
            if prev != 0:
                delta = (curr / prev - 1.0) * 100.0
                caption += f" | variação entre referências: {delta:+.1f}%"
        except (TypeError, ValueError):
            pass

    st.caption(caption)


def line_chart(df, x, y, title, color=None):
    fig = px.line(df, x=x, y=y, color=color, markers=True, title=title)
    fig.update_layout(**BLACK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)


def bar_chart(df, x, y, title, color=None, orientation="v"):
    fig = px.bar(df, x=x, y=y, color=color, title=title, orientation=orientation)
    fig.update_layout(**BLACK_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)


def render_validation_status(issues, metadata):
    errors = [i for i in issues if i["severity"] == "error"]
    warnings = [i for i in issues if i["severity"] == "warning"]

    status = str(metadata.get("publication_status", "unknown")).lower()
    if status != "validated" or errors:
        st.error(
            "Snapshot em revisão epidemiológica. "
            "Existem inconsistências bloqueantes ou o conjunto ainda não foi promovido para 'validated'. "
            "Não utilizar estes resultados como base isolada para decisão."
        )
    elif warnings:
        st.warning("Snapshot validado com alertas de qualidade/atualização que devem ser considerados na interpretação.")
    else:
        st.success("Snapshot aprovado nos gates automatizados disponíveis.")

    if issues:
        with st.expander(f"Qualidade dos dados — {len(errors)} erro(s), {len(warnings)} alerta(s)"):
            for item in issues:
                prefix = "ERRO" if item["severity"] == "error" else "ALERTA"
                st.write(f"**{prefix} · {item['scope']} · {item['code']}** — {item['message']}")


def main():
    required_files = build_required_files()
    missing = check_files(required_files)
    if missing:
        st.error("Arquivos públicos ausentes: " + ", ".join(missing))
        st.info("O app procura primeiro em data_public/ e depois na raiz do repositório.")
        st.stop()

    required_files, kpis, metadata, weekly, risk, risk_candidate, silent, virology, forecast, or_obito, or_uti = load_public_data()

    issues = validate_loaded_data(
        metadata=metadata,
        kpis=kpis,
        weekly=weekly,
        risk=risk,
        forecast=forecast,
        or_obito=or_obito,
        or_uti=or_uti,
        risk_candidate=risk_candidate,
    )

    st.title("Painel SRAG Público")
    st.caption("Camada pública: somente agregados; microdados do SIVEP-Gripe não são publicados neste repositório.")
    render_validation_status(issues, metadata)

    c1, c2, c3, c4 = st.columns(4)
    c1.write(f"**Ano de referência:** {metadata.get('year', 'NA')}")
    c2.write(f"**SE declarada como estável:** {metadata.get('stable_week', 'NA')}")
    c3.write(f"**Snapshot gerado em:** {metadata.get('generated_at', 'NA')}")
    c4.write(f"**Status:** {metadata.get('publication_status', 'NA')}")

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
    for i, (label, key, is_pct) in enumerate(labels):
        with cols[i % 3]:
            metric_card(
                label,
                kpis.get(key),
                ref_week=weekly_ref.get("SE_NOTIF"),
                ref_value=weekly_value(weekly_ref, key),
                prev_week=weekly_prev.get("SE_NOTIF"),
                prev_value=weekly_value(weekly_prev, key),
                is_percent=is_pct,
            )

    st.caption(
        "Os cartões exibem o valor acumulado disponível. Quando há referência semanal, "
        "a comparação entre semanas aparece separadamente na legenda para evitar misturar grandezas."
    )

    st.divider()

    tabs = st.tabs([
        "Resumo",
        "Risco e Silêncio",
        "Virologia",
        "Nowcasting e Forecast",
        "Odds Ratio",
        "Qualidade e Arquivos",
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
        st.subheader("Território — incidência auditada")
        st.info(
            "A incidência abaixo foi recalculada com população IBGE 2026. "
            "O score de risco legado permanece bloqueado e não participa desta ordenação."
        )

        if not risk_candidate.empty:
            candidate = risk_candidate.copy()
            candidate["incidencia_100k"] = pd.to_numeric(candidate["incidencia_100k"], errors="coerce")
            candidate["incidencia_100k_legacy"] = pd.to_numeric(
                candidate["incidencia_100k_legacy"], errors="coerce"
            )
            candidate["diferenca_incidencia"] = (
                candidate["incidencia_100k_legacy"] - candidate["incidencia_100k"]
            )

            audited_view = candidate.sort_values("incidencia_100k", ascending=False)
            bar_chart(
                audited_view.head(20),
                "NM_MUN",
                "incidencia_100k",
                "Top 20 municípios por incidência recalculada (/100 mil)",
            )

            display_cols = [
                "codigo_ibge",
                "NM_MUN",
                "populacao",
                "notificacoes",
                "casos_recentes",
                "incidencia_100k",
                "incidencia_recente_100k",
                "incidencia_100k_legacy",
                "diferenca_incidencia",
                "score_v2_status",
            ]
            st.dataframe(
                audited_view[[c for c in display_cols if c in audited_view.columns]].head(50),
                use_container_width=True,
            )
        else:
            st.warning("Artefato territorial auditado ainda não disponível.")

        st.markdown("**Score de risco e silêncio epidemiológico**")
        st.warning(
            "Bloqueados nesta versão. O score legado foi calculado sobre denominadores inconsistentes "
            "e sua fórmula original não está documentada no repositório. "
            "O modelo v2 está em calibração e será liberado somente após backtesting."
        )

    with tabs[2]:
        st.subheader("Virologia")
        if not virology.empty:
            identified = virology[
                ~virology["virus"].astype("string").str.contains("Não identificado", case=False, na=False)
            ]
            bar_chart(identified.head(15), "virus", "casos", "Vírus identificados")
            st.dataframe(virology, use_container_width=True)
        else:
            st.info("Sem resumo virológico.")

    with tabs[3]:
        st.subheader("Nowcasting e forecasting")
        forecast_blocked = has_errors(issues, {"forecast", "temporal"})
        if forecast_blocked:
            st.warning(
                "Forecast bloqueado enquanto a referência temporal do snapshot permanecer inconsistente. "
                "Previsões antigas não devem ser apresentadas como cenário atual."
            )
        elif not forecast.empty:
            sub = forecast[forecast["metrica"] == "notificacoes"].copy()
            if not sub.empty:
                bar_chart(sub, "horizonte_dias", "valor_esperado", "Forecast de notificações")
            st.dataframe(forecast, use_container_width=True)
        else:
            st.info("Sem forecast público.")

    with tabs[4]:
        st.subheader("Odds Ratio")
        st.caption(
            "Medidas de associação. Não interpretar como causalidade. "
            "A v2 exige documentação de população, referência, método e classificação bruto/ajustado."
        )
        cc = st.columns(2)
        with cc[0]:
            st.markdown("**Odds Ratio para óbito**")
            if has_errors(issues, {"or_obito"}):
                st.warning("Tabela bloqueada por inconsistência estatística.")
            else:
                st.dataframe(or_obito, use_container_width=True)
        with cc[1]:
            st.markdown("**Odds Ratio para UTI**")
            if has_errors(issues, {"or_uti"}):
                st.warning("Tabela bloqueada por inconsistência estatística.")
            else:
                st.dataframe(or_uti, use_container_width=True)

    with tabs[5]:
        st.subheader("Qualidade e proveniência")
        st.write(f"**Sistema-fonte declarado:** {metadata.get('source_system', 'NA')}")
        st.write(f"**Referência populacional requerida:** {metadata.get('population_reference_required', 'NA')}")
        st.write(f"**Versão-alvo:** {metadata.get('next_version', 'NA')}")

        if issues:
            st.dataframe(pd.DataFrame(issues), use_container_width=True)

        st.markdown("**Arquivos públicos localizados**")
        for key, path in required_files.items():
            st.write(f"- {key}: {path.name}")


if __name__ == "__main__":
    main()
