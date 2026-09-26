# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


@dataclass(frozen=True)
class SivepConfig:
    reference_year: int
    residence_uf_field: str
    residence_uf_value: str
    municipality_code_field: str
    symptom_week_field: str
    symptom_date_field: str
    hospital_field: str
    icu_field: str
    outcome_field: str
    stable_lag_weeks: int


def load_config(path: Path) -> SivepConfig:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return SivepConfig(
        reference_year=int(raw["reference_year"]),
        residence_uf_field=raw["territorial_scope"]["residence_uf_field"],
        residence_uf_value=raw["territorial_scope"]["residence_uf_value"],
        municipality_code_field=raw["territorial_scope"]["municipality_code_candidates"][0],
        symptom_week_field=raw["time"]["symptom_week_field"],
        symptom_date_field=raw["time"]["symptom_date_field"],
        hospital_field=raw["severity"]["hospital_field"],
        icu_field=raw["severity"]["icu_field"],
        outcome_field=raw["severity"]["outcome_field"],
        stable_lag_weeks=int(raw["time"]["stable_week_policy"]["lag_weeks"]),
    )


def detect_text_format(path: Path) -> tuple[str, str]:
    with path.open("rb") as handle:
        sample = handle.read(65536)
    encoding = "utf-8-sig"
    try:
        text = sample.decode(encoding)
    except UnicodeDecodeError:
        encoding = "latin-1"
        text = sample.decode(encoding)

    first_line = text.splitlines()[0] if text.splitlines() else ""
    candidates = [";", ",", "\t", "|"]
    counts = {sep: first_line.count(sep) for sep in candidates}
    delimiter = max(counts, key=counts.get)
    if counts[delimiter] == 0:
        raise ValueError("Não foi possível detectar o delimitador do CSV SIVEP.")
    return encoding, delimiter


def digits(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return re.sub(r"\D", "", text)


def normalize_week(value: object, reference_year: int) -> int | None:
    d = digits(value)
    if not d:
        return None
    # SEM_PRI é usualmente AAAASS; aceitar também SS.
    if len(d) >= 6:
        year = int(d[:4])
        week = int(d[-2:])
        if year != reference_year:
            return None
    else:
        week = int(d[-2:])
    if not 1 <= week <= 53:
        return None
    return week


def ibge7_to_sivep6(value: object) -> str:
    code = digits(value)
    if len(code) != 7 or not code.startswith("51"):
        raise ValueError(f"Código IBGE municipal inválido para MT: {value}")
    return code[:6]


def municipality_reference(path: Path) -> pd.DataFrame:
    ref = pd.read_csv(path, dtype={"codigo_ibge": "string"})
    required = {"codigo_ibge", "municipio", "populacao"}
    missing = required.difference(ref.columns)
    if missing:
        raise ValueError(f"Referência municipal sem colunas: {sorted(missing)}")
    if len(ref) != 142:
        raise ValueError(f"Referência municipal deve conter 142 municípios; encontrados {len(ref)}.")

    ref = ref.copy()
    ref["codigo_ibge"] = ref["codigo_ibge"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(7)
    ref["codigo_sivep_6"] = ref["codigo_ibge"].map(ibge7_to_sivep6)

    if ref["codigo_sivep_6"].duplicated().any():
        raise ValueError("Prefixo municipal IBGE de 6 dígitos não é único na referência.")
    return ref


def iter_sivep_chunks(path: Path, config: SivepConfig, chunksize: int = 100_000) -> Iterable[pd.DataFrame]:
    encoding, sep = detect_text_format(path)
    required = [
        config.residence_uf_field,
        config.municipality_code_field,
        config.symptom_week_field,
        config.symptom_date_field,
        config.hospital_field,
        config.icu_field,
        config.outcome_field,
    ]

    header = pd.read_csv(path, sep=sep, encoding=encoding, nrows=0)
    missing = [c for c in required if c not in header.columns]
    if missing:
        raise ValueError(f"Banco SIVEP sem campos obrigatórios para o P1: {missing}")

    for chunk in pd.read_csv(
        path,
        sep=sep,
        encoding=encoding,
        dtype="string",
        usecols=required,
        chunksize=chunksize,
        low_memory=False,
    ):
        yield chunk


def build_mt_aggregates(
    sivep_path: Path,
    population_path: Path,
    config_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    config = load_config(config_path)
    ref = municipality_reference(population_path)
    ref6 = ref.set_index("codigo_sivep_6")[["codigo_ibge", "municipio", "populacao"]]

    weekly_parts: list[pd.DataFrame] = []
    municipal_counts: dict[str, dict[str, int]] = {}
    municipal_weekly_counts: dict[tuple[str, int], dict[str, int]] = {}
    total_rows = 0
    mt_rows = 0
    invalid_municipality = 0
    invalid_week = 0

    for chunk in iter_sivep_chunks(sivep_path, config):
        total_rows += len(chunk)

        uf = chunk[config.residence_uf_field].astype("string").str.strip().str.upper()
        chunk = chunk.loc[uf == config.residence_uf_value].copy()
        mt_rows += len(chunk)
        if chunk.empty:
            continue

        chunk["codigo_sivep_6"] = chunk[config.municipality_code_field].map(digits).str[:6]
        chunk["SE"] = chunk[config.symptom_week_field].map(
            lambda x: normalize_week(x, config.reference_year)
        )

        valid_code = chunk["codigo_sivep_6"].isin(ref6.index)
        invalid_municipality += int((~valid_code).sum())
        chunk = chunk.loc[valid_code].copy()

        invalid_week += int(chunk["SE"].isna().sum())

        chunk["hospitalizado"] = chunk[config.hospital_field].astype("string").str.strip().eq("1").astype(int)
        chunk["uti"] = chunk[config.icu_field].astype("string").str.strip().eq("1").astype(int)
        outcome = chunk[config.outcome_field].astype("string").str.strip()
        chunk["obito"] = outcome.eq("2").astype(int)
        chunk["cura"] = outcome.eq("1").astype(int)

        w = (
            chunk.dropna(subset=["SE"])
            .groupby("SE", as_index=False)
            .agg(
                casos=("codigo_sivep_6", "size"),
                hospitalizacoes=("hospitalizado", "sum"),
                uti=("uti", "sum"),
                obitos=("obito", "sum"),
                curas=("cura", "sum"),
            )
        )
        weekly_parts.append(w)

        m = (
            chunk.groupby("codigo_sivep_6", as_index=False)
            .agg(
                casos=("codigo_sivep_6", "size"),
                hospitalizacoes=("hospitalizado", "sum"),
                uti=("uti", "sum"),
                obitos=("obito", "sum"),
                curas=("cura", "sum"),
            )
        )

        mw = (
            chunk.dropna(subset=["SE"])
            .groupby(["codigo_sivep_6", "SE"], as_index=False)
            .agg(
                casos=("codigo_sivep_6", "size"),
                hospitalizacoes=("hospitalizado", "sum"),
                uti=("uti", "sum"),
                obitos=("obito", "sum"),
                curas=("cura", "sum"),
            )
        )
        for row in mw.itertuples(index=False):
            key = (row.codigo_sivep_6, int(row.SE))
            acc = municipal_weekly_counts.setdefault(
                key,
                {"casos": 0, "hospitalizacoes": 0, "uti": 0, "obitos": 0, "curas": 0},
            )
            for field in ("casos", "hospitalizacoes", "uti", "obitos", "curas"):
                acc[field] += int(getattr(row, field))
        for row in m.itertuples(index=False):
            acc = municipal_counts.setdefault(
                row.codigo_sivep_6,
                {"casos": 0, "hospitalizacoes": 0, "uti": 0, "obitos": 0, "curas": 0},
            )
            for field in ("casos", "hospitalizacoes", "uti", "obitos", "curas"):
                acc[field] += int(getattr(row, field))

    if weekly_parts:
        weekly = pd.concat(weekly_parts, ignore_index=True)
        weekly = (
            weekly.groupby("SE", as_index=False)[
                ["casos", "hospitalizacoes", "uti", "obitos", "curas"]
            ]
            .sum()
            .sort_values("SE")
            .reset_index(drop=True)
        )
        max_observed = int(weekly["SE"].max())
        complete_weeks = pd.DataFrame({"SE": list(range(1, max_observed + 1))})
        weekly = complete_weeks.merge(weekly, on="SE", how="left")
        for field in ("casos", "hospitalizacoes", "uti", "obitos", "curas"):
            weekly[field] = weekly[field].fillna(0).astype(int)
    else:
        weekly = pd.DataFrame(
            columns=["SE", "casos", "hospitalizacoes", "uti", "obitos", "curas"]
        )

    municipal = ref[["codigo_ibge", "codigo_sivep_6", "municipio", "populacao"]].copy()
    for field in ("casos", "hospitalizacoes", "uti", "obitos", "curas"):
        municipal[field] = municipal["codigo_sivep_6"].map(
            lambda code: municipal_counts.get(code, {}).get(field, 0)
        ).astype(int)

    municipal["incidencia_srag_100k"] = municipal["casos"] / municipal["populacao"] * 100000.0
    municipal["hospitalizacao_100k"] = municipal["hospitalizacoes"] / municipal["populacao"] * 100000.0
    municipal["uti_100k"] = municipal["uti"] / municipal["populacao"] * 100000.0
    municipal["obito_100k"] = municipal["obitos"] / municipal["populacao"] * 100000.0

    if len(municipal) != 142 or municipal["codigo_ibge"].duplicated().any():
        raise ValueError("Agregado municipal final não preservou os 142 códigos IBGE únicos.")

    max_week = int(weekly["SE"].max()) if not weekly.empty else None

    if max_week is not None:
        observed_rows = []
        ref_lookup = ref.set_index("codigo_sivep_6")
        for (code, week), values in sorted(
            municipal_weekly_counts.items(),
            key=lambda item: (item[0][1], item[0][0]),
        ):
            ref_row = ref_lookup.loc[code]
            observed_rows.append({
                "codigo_ibge": ref_row["codigo_ibge"],
                "codigo_sivep_6": code,
                "municipio": ref_row["municipio"],
                "populacao": int(ref_row["populacao"]),
                "SE": int(week),
                **values,
            })

        observed = pd.DataFrame(observed_rows)
        weeks = pd.DataFrame({"SE": list(range(1, max_week + 1))})
        base = ref[["codigo_ibge", "codigo_sivep_6", "municipio", "populacao"]].copy()
        base["_join"] = 1
        weeks["_join"] = 1
        municipal_weekly = base.merge(weeks, on="_join", how="inner").drop(columns="_join")

        if not observed.empty:
            municipal_weekly = municipal_weekly.merge(
                observed[[
                    "codigo_ibge",
                    "SE",
                    "casos",
                    "hospitalizacoes",
                    "uti",
                    "obitos",
                    "curas",
                ]],
                on=["codigo_ibge", "SE"],
                how="left",
                validate="one_to_one",
            )
        else:
            for field in ("casos", "hospitalizacoes", "uti", "obitos", "curas"):
                municipal_weekly[field] = 0

        for field in ("casos", "hospitalizacoes", "uti", "obitos", "curas"):
            municipal_weekly[field] = municipal_weekly[field].fillna(0).astype(int)

        municipal_weekly["incidencia_srag_100k"] = (
            municipal_weekly["casos"] / municipal_weekly["populacao"] * 100000.0
        )
        municipal_weekly["hospitalizacao_100k"] = (
            municipal_weekly["hospitalizacoes"] / municipal_weekly["populacao"] * 100000.0
        )
        municipal_weekly["uti_100k"] = (
            municipal_weekly["uti"] / municipal_weekly["populacao"] * 100000.0
        )
        municipal_weekly["obito_100k"] = (
            municipal_weekly["obitos"] / municipal_weekly["populacao"] * 100000.0
        )
        municipal_weekly = municipal_weekly.sort_values(
            ["SE", "codigo_ibge"]
        ).reset_index(drop=True)

        if municipal_weekly.duplicated(["codigo_ibge", "SE"]).any():
            raise ValueError("Agregado municipal semanal contém chave codigo_ibge+SE duplicada.")
        expected_rows = 142 * max_week
        if len(municipal_weekly) != expected_rows:
            raise ValueError(
                f"Agregado municipal semanal incompleto: {len(municipal_weekly)} linhas; "
                f"esperado {expected_rows} (142 municípios x {max_week} SE)."
            )
    else:
        municipal_weekly = pd.DataFrame(columns=[
            "codigo_ibge",
            "codigo_sivep_6",
            "municipio",
            "populacao",
            "SE",
            "casos",
            "hospitalizacoes",
            "uti",
            "obitos",
            "curas",
            "incidencia_srag_100k",
            "hospitalizacao_100k",
            "uti_100k",
            "obito_100k",
        ])

    stable_week = None
    if max_week is not None:
        stable_week = max(1, max_week - config.stable_lag_weeks)

    metadata = {
        "reference_year": config.reference_year,
        "source_rows": int(total_rows),
        "mt_residence_rows": int(mt_rows),
        "invalid_municipality_rows": int(invalid_municipality),
        "invalid_week_rows": int(invalid_week),
        "max_observed_week": max_week,
        "stable_week_provisional": stable_week,
        "stable_week_lag": config.stable_lag_weeks,
        "stable_week_status": "provisional_requires_backtesting",
        "municipality_count": 142,
        "municipal_weekly_rows": int(len(municipal_weekly)),
        "population_total": int(municipal["populacao"].sum()),
        "territorial_basis": "residence",
    }

    return weekly, municipal, municipal_weekly, metadata
