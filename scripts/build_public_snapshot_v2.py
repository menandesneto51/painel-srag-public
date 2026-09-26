# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(ROOT))

from src.epi_calendar import epidemiological_week_start
DEFAULT_CANDIDATE = ROOT / "data_candidate"
DEFAULT_OUTPUT = DEFAULT_CANDIDATE / "public_snapshot"


def safe_percent(numerator: float, denominator: float) -> float | None:
    if denominator is None or denominator <= 0:
        return None
    return float(numerator / denominator * 100.0)


def load_json(path: Path, required: bool = True) -> dict:
    if not path.exists():
        if required:
            raise FileNotFoundError(path)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def read_optional_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8-sig")


def build_weekly(
    weekly_raw: pd.DataFrame,
    year: int,
) -> pd.DataFrame:
    required = {"SE", "casos", "hospitalizacoes", "uti", "obitos", "curas"}
    missing = required.difference(weekly_raw.columns)
    if missing:
        raise ValueError(f"Agregado semanal sem colunas obrigatórias: {sorted(missing)}")

    weekly = weekly_raw.copy()
    for col in ("SE", "casos", "hospitalizacoes", "uti", "obitos", "curas"):
        weekly[col] = pd.to_numeric(weekly[col], errors="coerce")
    weekly = weekly.dropna(subset=["SE"]).copy()
    weekly["SE"] = weekly["SE"].astype(int)

    weekly["ANO_NOTIF"] = year
    weekly["SE_NOTIF"] = weekly["SE"]
    weekly["SEMANA_NOTIF_INICIO"] = weekly["SE"].map(
        lambda week: epidemiological_week_start(year, int(week)).isoformat()
    )
    weekly["notificacoes"] = weekly["casos"]
    weekly["cura"] = weekly["curas"]
    weekly["taxa_uti_hosp_percent"] = weekly.apply(
        lambda row: safe_percent(row["uti"], row["hospitalizacoes"]),
        axis=1,
    )
    weekly["letalidade_casos_percent"] = weekly.apply(
        lambda row: safe_percent(row["obitos"], row["casos"]),
        axis=1,
    )

    cols = [
        "ANO_NOTIF",
        "SE_NOTIF",
        "SEMANA_NOTIF_INICIO",
        "notificacoes",
        "casos",
        "hospitalizacoes",
        "uti",
        "obitos",
        "cura",
        "taxa_uti_hosp_percent",
        "letalidade_casos_percent",
    ]
    return weekly[cols].sort_values("SE_NOTIF").reset_index(drop=True)


def determine_stable_weeks(
    pipeline_metadata: dict,
    stability: dict,
) -> tuple[int, int]:
    max_week = pipeline_metadata.get("max_observed_week")
    if max_week is None:
        raise ValueError("max_observed_week ausente no metadata do pipeline.")

    cases = stability.get("provisional_case_stable_week")
    outcomes = stability.get("provisional_outcome_stable_week")
    if cases is None:
        cases = pipeline_metadata.get("stable_week_provisional")
    if outcomes is None:
        outcomes = cases

    cases = int(cases)
    outcomes = int(outcomes)
    max_week = int(max_week)
    if not (1 <= cases <= max_week):
        raise ValueError(f"stable_week de casos inválida: {cases}; max={max_week}")
    if not (1 <= outcomes <= max_week):
        raise ValueError(f"stable_week de desfechos inválida: {outcomes}; max={max_week}")
    return cases, outcomes


def build_territorial(
    municipal: pd.DataFrame,
    municipal_weekly: pd.DataFrame,
    stable_week_cases: int,
    recent_window_weeks: int = 2,
) -> pd.DataFrame:
    required = {
        "codigo_ibge",
        "municipio",
        "populacao",
        "casos",
        "hospitalizacoes",
        "uti",
        "obitos",
        "curas",
    }
    missing = required.difference(municipal.columns)
    if missing:
        raise ValueError(f"Agregado municipal sem colunas: {sorted(missing)}")

    territorial = municipal.copy()
    territorial["codigo_ibge"] = (
        territorial["codigo_ibge"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(7)
    )
    if len(territorial) != 142 or territorial["codigo_ibge"].duplicated().any():
        raise ValueError("Agregado municipal deve conter 142 códigos IBGE únicos.")

    start_week = max(1, stable_week_cases - recent_window_weeks + 1)
    recent = municipal_weekly.copy()
    if not recent.empty:
        recent["codigo_ibge"] = (
            recent["codigo_ibge"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(7)
        )
        recent["SE"] = pd.to_numeric(recent["SE"], errors="coerce")
        recent = recent.loc[
            recent["SE"].between(start_week, stable_week_cases, inclusive="both")
        ]
        recent_counts = recent.groupby("codigo_ibge")["casos"].sum()
    else:
        recent_counts = pd.Series(dtype=float)

    territorial["notificacoes"] = pd.to_numeric(territorial["casos"], errors="coerce").fillna(0).astype(int)
    territorial["casos_recentes"] = (
        territorial["codigo_ibge"].map(recent_counts).fillna(0).astype(int)
    )
    territorial["populacao"] = pd.to_numeric(territorial["populacao"], errors="raise").astype(int)
    territorial["incidencia_100k"] = (
        territorial["notificacoes"] / territorial["populacao"] * 100000.0
    )
    territorial["incidencia_recente_100k"] = (
        territorial["casos_recentes"] / territorial["populacao"] * 100000.0
    )
    territorial["tx_uti_percent"] = territorial.apply(
        lambda row: safe_percent(row["uti"], row["hospitalizacoes"]),
        axis=1,
    )
    territorial["obito_casos_percent"] = territorial.apply(
        lambda row: safe_percent(row["obitos"], row["casos"]),
        axis=1,
    )
    territorial["score_v2_status"] = "under_calibration"
    territorial["recent_window_start_se"] = start_week
    territorial["recent_window_end_se"] = stable_week_cases

    return territorial[[
        "codigo_ibge",
        "municipio",
        "populacao",
        "notificacoes",
        "casos_recentes",
        "incidencia_100k",
        "incidencia_recente_100k",
        "hospitalizacoes",
        "uti",
        "obitos",
        "curas",
        "tx_uti_percent",
        "obito_casos_percent",
        "score_v2_status",
        "recent_window_start_se",
        "recent_window_end_se",
    ]].rename(columns={"municipio": "NM_MUN"})


def weekly_record(row: pd.Series | None) -> dict:
    if row is None:
        return {}
    result = {}
    for key, value in row.to_dict().items():
        if pd.isna(value):
            result[key] = None
            continue
        if hasattr(value, "item"):
            try:
                value = value.item()
            except ValueError:
                pass
        if isinstance(value, bool):
            result[key] = value
        elif isinstance(value, int):
            result[key] = value
        elif isinstance(value, float):
            result[key] = int(value) if value.is_integer() else value
        else:
            result[key] = str(value)
    return result


def build_kpis(
    weekly: pd.DataFrame,
    stable_week_cases: int,
) -> dict:
    totals = {
        "notificacoes": int(weekly["notificacoes"].sum()),
        "casos": int(weekly["casos"].sum()),
        "hospitalizacoes": int(weekly["hospitalizacoes"].sum()),
        "uti": int(weekly["uti"].sum()),
        "obitos": int(weekly["obitos"].sum()),
        "cura": int(weekly["cura"].sum()),
    }
    totals["taxa_uti_hosp_percent"] = safe_percent(
        totals["uti"], totals["hospitalizacoes"]
    )
    totals["letalidade_hosp_percent"] = None
    totals["taxa_envio_lab_percent"] = None

    ref_rows = weekly.loc[weekly["SE_NOTIF"] == stable_week_cases]
    reference = ref_rows.iloc[0] if not ref_rows.empty else None
    previous_rows = weekly.loc[weekly["SE_NOTIF"] < stable_week_cases].sort_values("SE_NOTIF")
    previous = previous_rows.iloc[-1] if not previous_rows.empty else None

    totals["weekly_reference"] = weekly_record(reference)
    totals["weekly_previous"] = weekly_record(previous)
    return totals


def build_virology_summary(weekly_virology: pd.DataFrame) -> pd.DataFrame:
    columns = ["virus", "casos", "deteccoes", "participacao_percent"]
    if weekly_virology.empty:
        return pd.DataFrame(columns=columns)
    required = {"virus", "deteccoes"}
    if not required.issubset(weekly_virology.columns):
        raise ValueError("Virologia semanal sem virus/deteccoes.")

    grouped = (
        weekly_virology.groupby("virus", as_index=False)["deteccoes"]
        .sum()
        .sort_values("deteccoes", ascending=False)
    )
    total = float(grouped["deteccoes"].sum())
    grouped["casos"] = grouped["deteccoes"]
    grouped["participacao_percent"] = (
        grouped["deteccoes"] / total * 100.0 if total > 0 else 0.0
    )
    return grouped[columns]


def build_or_public(raw: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "Variável",
        "Expostos",
        "OR",
        "IC95% inferior",
        "IC95% superior",
        "Expostos com desfecho",
        "Expostos sem desfecho",
        "Não expostos com desfecho",
        "Não expostos sem desfecho",
        "N válido",
        "Missing exposição",
        "Modelo",
        "Correção célula zero",
    ]
    if raw.empty:
        return pd.DataFrame(columns=cols)

    rename = {
        "variavel": "Variável",
        "expostos_total": "Expostos",
        "OR_bruta": "OR",
        "IC95_inf": "IC95% inferior",
        "IC95_sup": "IC95% superior",
        "expostos_com_desfecho": "Expostos com desfecho",
        "expostos_sem_desfecho": "Expostos sem desfecho",
        "nao_expostos_com_desfecho": "Não expostos com desfecho",
        "nao_expostos_sem_desfecho": "Não expostos sem desfecho",
        "n_valido": "N válido",
        "missing_exposicao": "Missing exposição",
        "modelo": "Modelo",
        "correcao_celula_zero_0_5": "Correção célula zero",
    }
    result = raw.rename(columns=rename)
    return result[[col for col in cols if col in result.columns]]


def build_snapshot(
    candidate_dir: Path,
    output_dir: Path,
    sources_path: Path,
    recent_window_weeks: int = 2,
) -> dict:
    weekly_raw = pd.read_csv(candidate_dir / "weekly_srag_mt_2026.csv")
    municipal = pd.read_csv(
        candidate_dir / "municipal_srag_mt_2026.csv",
        dtype={"codigo_ibge": "string"},
    )
    municipal_weekly = pd.read_csv(
        candidate_dir / "municipal_weekly_srag_mt_2026.csv",
        dtype={"codigo_ibge": "string"},
    )
    pipeline_metadata = load_json(candidate_dir / "sivep_mt_2026_metadata.json")
    stability = load_json(
        candidate_dir / "stability_delay_estimate.json",
        required=False,
    )
    sources = load_json(sources_path)
    year = int(pipeline_metadata.get("reference_year", 2026))

    stable_cases, stable_outcomes = determine_stable_weeks(
        pipeline_metadata, stability
    )

    weekly = build_weekly(weekly_raw, year)
    territorial = build_territorial(
        municipal,
        municipal_weekly,
        stable_cases,
        recent_window_weeks=recent_window_weeks,
    )
    kpis = build_kpis(weekly, stable_cases)

    virology_weekly = read_optional_csv(
        candidate_dir / "virology_weekly_mt_2026.csv"
    )
    virology = build_virology_summary(virology_weekly)

    or_obito = build_or_public(
        read_optional_csv(candidate_dir / "or_obito_crude_v2.csv")
    )
    or_uti = build_or_public(
        read_optional_csv(candidate_dir / "or_uti_crude_v2.csv")
    )

    forecast = pd.DataFrame(columns=[
        "metrica",
        "horizonte_dias",
        "data_inicial",
        "data_final",
        "valor_esperado",
        "ic95_inf",
        "ic95_sup",
        "valor_minimo",
        "valor_maximo",
    ])
    silent = pd.DataFrame(columns=[
        "codigo_ibge",
        "NM_MUN",
        "silence_status",
    ])

    source = sources["sources"]["sivep_gripe_2026"]
    metadata = {
        "year": year,
        "stable_week": stable_cases,
        "stable_week_cases": stable_cases,
        "stable_week_outcomes": stable_outcomes,
        "stable_week_status": stability.get(
            "status",
            pipeline_metadata.get("stable_week_status", "provisional"),
        ),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_system": "SIVEP-Gripe",
        "source_resource_date": source.get("resource_date"),
        "source_resource_id": source.get("resource_id"),
        "source_url": source.get("url"),
        "population_reference": "IBGE 2026",
        "population_total": int(territorial["populacao"].sum()),
        "municipality_count": int(len(territorial)),
        "publication_status": "under_review",
        "validation_status": "under_review",
        "risk_model_status": "under_calibration",
        "forecast_status": "blocked_not_reprocessed",
        "silence_model_status": "blocked_not_recalibrated",
        "or_model": "crude_2x2" if (not or_obito.empty or not or_uti.empty) else "blocked_not_reprocessed",
        "virology_status": "candidate" if not virology.empty else "blocked_not_reprocessed",
        "recent_window_weeks": recent_window_weeks,
        "next_version": "v2.0.0",
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(output_dir / "weekly_summary.csv", index=False, encoding="utf-8")
    territorial.to_csv(output_dir / "risk_summary.csv", index=False, encoding="utf-8")
    territorial.to_csv(
        output_dir / "risk_summary_v2_candidate.csv",
        index=False,
        encoding="utf-8",
    )
    silent.to_csv(output_dir / "silent_summary.csv", index=False, encoding="utf-8")
    virology.to_csv(output_dir / "virology_summary.csv", index=False, encoding="utf-8")
    forecast.to_csv(output_dir / "forecast_summary.csv", index=False, encoding="utf-8")
    or_obito.to_csv(output_dir / "or_obito_summary.csv", index=False, encoding="utf-8")
    or_uti.to_csv(output_dir / "or_uti_summary.csv", index=False, encoding="utf-8")
    (output_dir / "kpis.json").write_text(
        json.dumps(kpis, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output_dir / "metadata_public.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Monta snapshot público v2 a partir dos artefatos candidatos.")
    parser.add_argument("--candidate-dir", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--sources",
        type=Path,
        default=ROOT / "config" / "sources.json",
    )
    parser.add_argument("--recent-window-weeks", type=int, default=2)
    args = parser.parse_args()

    if args.recent_window_weeks < 1:
        raise ValueError("--recent-window-weeks deve ser >= 1")

    metadata = build_snapshot(
        args.candidate_dir,
        args.output_dir,
        args.sources,
        recent_window_weeks=args.recent_window_weeks,
    )
    print(json.dumps(metadata, ensure_ascii=False, indent=2))
    print(f"snapshot={args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
