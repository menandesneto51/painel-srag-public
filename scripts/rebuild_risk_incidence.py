# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RISK = ROOT / "risk_summary.csv"
DEFAULT_POP = ROOT / "reference" / "population_mt_2026.csv"
DEFAULT_OUT = ROOT / "data_public" / "risk_summary_v2_candidate.csv"
DEFAULT_AUDIT = ROOT / "reports" / "risk_denominator_audit.csv"


def norm_name(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.lower().strip().split())


def build_candidate(risk_path: Path, population_path: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    risk = pd.read_csv(risk_path, encoding="utf-8-sig")
    population = pd.read_csv(population_path, dtype={"codigo_ibge": "string"})

    if len(population) != 142:
        raise ValueError(f"Referência populacional deve conter 142 municípios; encontrados {len(population)}.")
    if population["codigo_ibge"].duplicated().any():
        raise ValueError("Referência populacional contém códigos IBGE duplicados.")
    if population["municipio"].duplicated().any():
        raise ValueError("Referência populacional contém municípios duplicados.")
    if int(population["populacao"].sum()) != 3_950_330:
        raise ValueError("Total populacional MT 2026 divergente de 3.950.330.")

    # Migração temporária do artefato legado: ele não possui código IBGE.
    # O pipeline definitivo deverá agregar SRAG já com código oficial.
    risk["_join_name"] = risk["NM_MUN"].map(norm_name)
    population["_join_name"] = population["municipio"].map(norm_name)

    merged = risk.merge(
        population[[
            "codigo_ibge",
            "municipio",
            "populacao",
            "ano_populacao",
            "data_referencia_populacao",
            "fonte_populacao",
            "_join_name",
        ]],
        on="_join_name",
        how="left",
        validate="one_to_one",
        indicator=True,
    )

    missing = merged.loc[merged["_merge"] != "both", "NM_MUN"].tolist()
    if missing:
        raise ValueError(f"Municípios sem correspondência populacional: {missing}")
    if len(merged) != 142:
        raise ValueError(f"Esperados 142 municípios no risk_summary legado; encontrados {len(merged)}.")

    for col in ("notificacoes", "casos_recentes", "incidencia_100k", "incidencia_recente_100k"):
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    merged["incidencia_100k_legacy"] = merged["incidencia_100k"]
    merged["incidencia_recente_100k_legacy"] = merged["incidencia_recente_100k"]

    merged["incidencia_100k"] = merged["notificacoes"] / merged["populacao"] * 100000.0
    merged["incidencia_recente_100k"] = merged["casos_recentes"] / merged["populacao"] * 100000.0

    merged["score_risco_srag_legacy"] = merged["score_risco_srag"]
    merged["classe_risco_srag_legacy"] = merged["classe_risco_srag"]
    merged["score_v2_status"] = "blocked"

    candidate_cols = [
        "codigo_ibge",
        "NM_MUN",
        "NM_RGI",
        "populacao",
        "ano_populacao",
        "data_referencia_populacao",
        "fonte_populacao",
        "notificacoes",
        "casos_recentes",
        "incidencia_100k",
        "incidencia_recente_100k",
        "incidencia_100k_legacy",
        "incidencia_recente_100k_legacy",
        "tx_uti_percent",
        "letalidade_percent",
        "score_risco_srag_legacy",
        "classe_risco_srag_legacy",
        "score_v2_status",
    ]

    candidate = merged[candidate_cols].copy()

    audit = candidate[[
        "codigo_ibge",
        "NM_MUN",
        "populacao",
        "notificacoes",
        "casos_recentes",
        "incidencia_100k_legacy",
        "incidencia_100k",
        "incidencia_recente_100k_legacy",
        "incidencia_recente_100k",
    ]].copy()
    audit["diferenca_abs"] = (
        audit["incidencia_100k_legacy"] - audit["incidencia_100k"]
    ).abs()
    audit["diferenca_recente_abs"] = (
        audit["incidencia_recente_100k_legacy"] - audit["incidencia_recente_100k"]
    ).abs()

    return candidate, audit


def main() -> int:
    parser = argparse.ArgumentParser(description="Reconstrói incidências municipais usando IBGE 2026.")
    parser.add_argument("--risk", type=Path, default=DEFAULT_RISK)
    parser.add_argument("--population", type=Path, default=DEFAULT_POP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    args = parser.parse_args()

    candidate, audit = build_candidate(args.risk, args.population)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    candidate.to_csv(args.out, index=False, encoding="utf-8")
    audit.to_csv(args.audit, index=False, encoding="utf-8")

    print(f"OK: {len(candidate)} municípios recalculados.")
    print(f"Candidate: {args.out}")
    print(f"Audit: {args.audit}")
    print("Maiores diferenças absolutas:")
    print(
        audit.sort_values("diferenca_abs", ascending=False)
        [["NM_MUN", "incidencia_100k_legacy", "incidencia_100k", "diferenca_abs"]]
        .head(15)
        .to_string(index=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
