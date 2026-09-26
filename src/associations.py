# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.sivep_pipeline import detect_text_format, digits, municipality_reference


def _text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def crude_or(a: int, b: int, c: int, d: int) -> dict:
    """2x2: a=E+D+, b=E+D-, c=E-D+, d=E-D-."""
    cells = [float(a), float(b), float(c), float(d)]
    corrected = any(x == 0 for x in cells)
    if corrected:
        cells = [x + 0.5 for x in cells]

    aa, bb, cc, dd = cells
    estimate = (aa * dd) / (bb * cc)
    se = math.sqrt(1.0 / aa + 1.0 / bb + 1.0 / cc + 1.0 / dd)
    log_or = math.log(estimate)
    low = math.exp(log_or - 1.96 * se)
    high = math.exp(log_or + 1.96 * se)

    return {
        "or": estimate,
        "ic95_inf": low,
        "ic95_sup": high,
        "zero_cell_correction": corrected,
    }


def _binary_from_spec(data: dict, spec: dict) -> bool | None:
    value = _text(data.get(spec["field"]))
    if value in set(map(str, spec["yes"])):
        return True
    if value in set(map(str, spec["no"])):
        return False
    return None


def _age_ge_60(data: dict, spec: dict) -> bool | None:
    age_raw = _text(data.get(spec["age_field"]))
    age_type = _text(data.get(spec["age_type_field"]))
    if not age_raw or age_type not in {"1", "2", "3"}:
        return None
    try:
        age = int(float(age_raw))
    except ValueError:
        return None
    if age < 0:
        return None
    if age_type in {"1", "2"}:
        return False
    return age >= 60


def build_crude_associations(
    sivep_path: Path,
    population_path: Path,
    config_path: Path,
    chunksize: int = 100_000,
) -> dict[str, pd.DataFrame]:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    territory = cfg["territorial_scope"]
    assoc = cfg["associations"]

    uf_field = territory["residence_uf_field"]
    mun_field = territory["municipality_code_candidates"][0]
    outcome_specs = assoc["outcomes"]
    exposure_specs = assoc["exposures"]

    fields = {uf_field, mun_field}
    for spec in outcome_specs.values():
        fields.add(spec["field"])
    for spec in exposure_specs.values():
        if "field" in spec:
            fields.add(spec["field"])
        if spec.get("derived") == "age_ge_60":
            fields.add(spec["age_field"])
            fields.add(spec["age_type_field"])
    required = sorted(fields)

    encoding, sep = detect_text_format(sivep_path)
    header = pd.read_csv(sivep_path, sep=sep, encoding=encoding, nrows=0)
    missing = [field for field in required if field not in header.columns]
    if missing:
        raise ValueError(f"Banco SIVEP sem campos para associações: {missing}")

    ref = municipality_reference(population_path)
    valid_codes = set(ref["codigo_sivep_6"].tolist())

    cells = {
        outcome: {exposure: defaultdict(int) for exposure in exposure_specs}
        for outcome in outcome_specs
    }

    reader = pd.read_csv(
        sivep_path,
        sep=sep,
        encoding=encoding,
        dtype="string",
        usecols=required,
        chunksize=chunksize,
        low_memory=False,
    )
    try:
        for chunk in reader:
            uf = chunk[uf_field].astype("string").str.strip().str.upper()
            chunk = chunk.loc[uf == territory["residence_uf_value"]].copy()
            if chunk.empty:
                continue

            chunk["codigo_sivep_6"] = chunk[mun_field].map(digits).str[:6]
            chunk = chunk.loc[chunk["codigo_sivep_6"].isin(valid_codes)].copy()
            if chunk.empty:
                continue

            for row in chunk.itertuples(index=False):
                data = row._asdict()

                outcomes: dict[str, bool | None] = {}
                for outcome_name, outcome_spec in outcome_specs.items():
                    value = _text(data.get(outcome_spec["field"]))
                    if value in set(map(str, outcome_spec["case_values"])):
                        outcomes[outcome_name] = True
                    elif value in set(map(str, outcome_spec["control_values"])):
                        outcomes[outcome_name] = False
                    else:
                        outcomes[outcome_name] = None

                exposures: dict[str, bool | None] = {}
                for exposure_name, exposure_spec in exposure_specs.items():
                    if exposure_spec.get("derived") == "age_ge_60":
                        exposures[exposure_name] = _age_ge_60(data, exposure_spec)
                    else:
                        exposures[exposure_name] = _binary_from_spec(data, exposure_spec)

                for outcome_name, outcome_value in outcomes.items():
                    if outcome_value is None:
                        continue
                    for exposure_name, exposure_value in exposures.items():
                        bucket = cells[outcome_name][exposure_name]
                        if exposure_value is None:
                            bucket["missing_exposure"] += 1
                            continue
                        if exposure_value and outcome_value:
                            bucket["a"] += 1
                        elif exposure_value and not outcome_value:
                            bucket["b"] += 1
                        elif not exposure_value and outcome_value:
                            bucket["c"] += 1
                        else:
                            bucket["d"] += 1
    finally:
        reader.close()

    outputs: dict[str, pd.DataFrame] = {}
    for outcome_name, exposures in cells.items():
        rows = []
        for exposure_name, bucket in exposures.items():
            a = int(bucket["a"])
            b = int(bucket["b"])
            c = int(bucket["c"])
            d = int(bucket["d"])
            total_valid = a + b + c + d

            if total_valid == 0:
                result = {
                    "or": None,
                    "ic95_inf": None,
                    "ic95_sup": None,
                    "zero_cell_correction": False,
                }
            else:
                result = crude_or(a, b, c, d)

            rows.append({
                "variavel": exposure_name,
                "desfecho": outcome_name,
                "expostos_com_desfecho": a,
                "expostos_sem_desfecho": b,
                "nao_expostos_com_desfecho": c,
                "nao_expostos_sem_desfecho": d,
                "expostos_total": a + b,
                "nao_expostos_total": c + d,
                "n_valido": total_valid,
                "missing_exposicao": int(bucket["missing_exposure"]),
                "OR_bruta": result["or"],
                "IC95_inf": result["ic95_inf"],
                "IC95_sup": result["ic95_sup"],
                "correcao_celula_zero_0_5": result["zero_cell_correction"],
                "modelo": "crude_2x2",
            })
        outputs[outcome_name] = pd.DataFrame(rows)

    return outputs
