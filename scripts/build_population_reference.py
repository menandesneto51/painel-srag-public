# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data_raw" / "estimativa_dou_2026.xlsx"
DEFAULT_OUTPUT = ROOT / "reference" / "population_mt_2026.csv"


def norm(value: object) -> str:
    text = "" if value is None else str(value)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\s+", " ", text).strip().upper()
    return text


def find_header_row(raw: pd.DataFrame) -> int:
    for idx, row in raw.iterrows():
        cells = [norm(v) for v in row.tolist()]
        joined = " | ".join(cells)
        has_uf = "COD. UF" in joined or "COD UF" in joined
        has_mun_code = "COD. MUNIC" in joined or "COD MUNIC" in joined
        has_name = "MUNICIPIO" in joined
        has_population = "POPULACAO" in joined
        if has_uf and has_mun_code and has_name and has_population:
            return int(idx)
    raise ValueError("Cabeçalho do arquivo IBGE não foi identificado de forma segura.")


def find_column(columns, predicates, label: str):
    normalized = {col: norm(col) for col in columns}
    matches = []
    for col, value in normalized.items():
        if all(predicate(value) for predicate in predicates):
            matches.append(col)
    if len(matches) != 1:
        raise ValueError(f"Não foi possível identificar unicamente a coluna {label}: {matches}")
    return matches[0]


def digits(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            return str(int(value))
        except Exception:
            pass
    return re.sub(r"\D", "", str(value))


def population_value(value: object) -> int | None:
    text = digits(value)
    return int(text) if text else None


def build_reference(input_path: Path, output_path: Path) -> pd.DataFrame:
    if not input_path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {input_path}. "
            "Execute antes: python scripts/download_official_sources.py --source ibge_population_2026"
        )

    raw = pd.read_excel(input_path, header=None, engine="openpyxl")
    header_row = find_header_row(raw)
    df = pd.read_excel(input_path, header=header_row, engine="openpyxl")

    uf_col = find_column(
        df.columns,
        [lambda x: "COD" in x, lambda x: "UF" in x, lambda x: "MUNIC" not in x],
        "código UF",
    )
    mun_code_col = find_column(
        df.columns,
        [lambda x: "COD" in x, lambda x: "MUNIC" in x],
        "código municipal",
    )
    mun_name_col = find_column(
        df.columns,
        [lambda x: "MUNIC" in x, lambda x: "COD" not in x],
        "nome do município",
    )
    pop_col = find_column(
        df.columns,
        [lambda x: "POPULACAO" in x],
        "população",
    )

    work = df[[uf_col, mun_code_col, mun_name_col, pop_col]].copy()
    work["uf_code"] = work[uf_col].map(digits)
    work["municipio_code_part"] = work[mun_code_col].map(digits)
    work["municipio"] = work[mun_name_col].astype("string").str.strip()
    work["populacao"] = work[pop_col].map(population_value)

    work = work[work["uf_code"] == "51"].copy()
    work = work[work["municipio"].notna() & work["populacao"].notna()].copy()

    work["codigo_ibge"] = (
        work["uf_code"].str.zfill(2)
        + work["municipio_code_part"].str.zfill(5)
    )

    out = work[["codigo_ibge", "municipio", "populacao"]].copy()
    out["codigo_ibge"] = out["codigo_ibge"].astype("string")
    out["populacao"] = out["populacao"].astype("int64")
    out["ano_populacao"] = 2026
    out["data_referencia_populacao"] = "2026-07-01"
    out["fonte_populacao"] = "IBGE - estimativas populacionais publicadas no DOU"

    if len(out) != 142:
        raise ValueError(f"Esperados 142 municípios de Mato Grosso; encontrados {len(out)}.")

    if out["codigo_ibge"].duplicated().any():
        duplicated = out.loc[out["codigo_ibge"].duplicated(keep=False), "codigo_ibge"].tolist()
        raise ValueError(f"Códigos IBGE duplicados: {duplicated}")

    if out["municipio"].duplicated().any():
        duplicated = out.loc[out["municipio"].duplicated(keep=False), "municipio"].tolist()
        raise ValueError(f"Municípios duplicados: {duplicated}")

    if (out["populacao"] <= 0).any():
        raise ValueError("Foram encontradas populações não positivas.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    out = out.sort_values(["municipio"]).reset_index(drop=True)
    out.to_csv(output_path, index=False, encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Constrói referência populacional oficial MT 2026.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    out = build_reference(args.input, args.output)
    print(f"OK: {len(out)} municípios gravados em {args.output}")
    print(f"População total da referência: {int(out['populacao'].sum()):,}".replace(",", "."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
