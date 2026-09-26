# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

from src.sivep_pipeline import (
    detect_text_format,
    digits,
    municipality_reference,
    normalize_week,
)


def _text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def build_virology_metrics(
    sivep_path: Path,
    population_path: Path,
    config_path: Path,
    chunksize: int = 100_000,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    territory = cfg["territorial_scope"]
    time_cfg = cfg["time"]
    virology = cfg["virology"]

    uf_field = territory["residence_uf_field"]
    mun_field = territory["municipality_code_candidates"][0]
    week_field = time_cfg["symptom_week_field"]
    year = int(cfg["reference_year"])

    molecular_field = virology["molecular_result_field"]
    influenza_positive_field = virology["influenza_positive_field"]
    influenza_type_field = virology["influenza_type_field"]
    other_positive_field = virology["other_virus_positive_field"]
    marker_fields = dict(virology["virus_markers"])

    required = [
        uf_field,
        mun_field,
        week_field,
        molecular_field,
        influenza_positive_field,
        influenza_type_field,
        other_positive_field,
        *marker_fields.values(),
    ]

    encoding, sep = detect_text_format(sivep_path)
    header = pd.read_csv(sivep_path, sep=sep, encoding=encoding, nrows=0)
    missing = [field for field in required if field not in header.columns]
    if missing:
        raise ValueError(f"Banco SIVEP sem campos virológicos obrigatórios: {missing}")

    ref = municipality_reference(population_path)
    ref_by6 = ref.set_index("codigo_sivep_6")
    valid_codes = set(ref_by6.index.tolist())

    weekly_totals: dict[int, Counter] = defaultdict(Counter)
    weekly_detections: dict[tuple[int, str], int] = defaultdict(int)

    municipal_totals: dict[tuple[str, int], Counter] = defaultdict(Counter)
    municipal_detections: dict[tuple[str, int, str], int] = defaultdict(int)

    mt_rows = 0
    invalid_municipality = 0
    invalid_week = 0
    total_agent_detections = 0
    records_with_multiple_agents = 0
    detectable_without_agent = 0

    available_values = set(map(str, virology["molecular_result_available_values"]))
    conclusive_values = set(map(str, virology["molecular_conclusive_values"]))
    detectable_value = str(virology["molecular_detectable_value"])
    marker_value = str(virology["marker_value"])
    flu_positive_value = str(virology["influenza_positive_value"])
    other_positive_value = str(virology["other_virus_positive_value"])
    flu_types = {str(k): v for k, v in virology["influenza_types"].items()}

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
        chunks = reader
        for chunk in chunks:
            uf = chunk[uf_field].astype("string").str.strip().str.upper()
            chunk = chunk.loc[uf == territory["residence_uf_value"]].copy()
            mt_rows += len(chunk)
            if chunk.empty:
                continue

            chunk["codigo_sivep_6"] = chunk[mun_field].map(digits).str[:6]
            valid_mun = chunk["codigo_sivep_6"].isin(valid_codes)
            invalid_municipality += int((~valid_mun).sum())
            chunk = chunk.loc[valid_mun].copy()
            if chunk.empty:
                continue

            chunk["SE"] = chunk[week_field].map(lambda x: normalize_week(x, year))
            invalid_week += int(chunk["SE"].isna().sum())
            chunk = chunk.dropna(subset=["SE"]).copy()
            if chunk.empty:
                continue

            chunk["SE"] = chunk["SE"].astype(int)

            for row in chunk.itertuples(index=False):
                data = row._asdict()
                code = str(data["codigo_sivep_6"])
                week = int(data["SE"])
                pcr_result = _text(data.get(molecular_field))

                weekly_totals[week]["registros"] += 1
                municipal_totals[(code, week)]["registros"] += 1

                if pcr_result in available_values:
                    weekly_totals[week]["pcr_resultado_disponivel"] += 1
                    municipal_totals[(code, week)]["pcr_resultado_disponivel"] += 1

                if pcr_result in conclusive_values:
                    weekly_totals[week]["pcr_conclusivo"] += 1
                    municipal_totals[(code, week)]["pcr_conclusivo"] += 1

                if pcr_result == "3":
                    weekly_totals[week]["pcr_inconclusivo"] += 1
                    municipal_totals[(code, week)]["pcr_inconclusivo"] += 1

                if pcr_result == detectable_value:
                    weekly_totals[week]["pcr_detectavel"] += 1
                    municipal_totals[(code, week)]["pcr_detectavel"] += 1

                agents: set[str] = set()

                flu_pos = _text(data.get(influenza_positive_field))
                flu_type = _text(data.get(influenza_type_field))
                if flu_pos == flu_positive_value and flu_type in flu_types:
                    agents.add(flu_types[flu_type])

                other_pos = _text(data.get(other_positive_field))
                if other_pos == other_positive_value:
                    for virus, field in marker_fields.items():
                        if _text(data.get(field)) == marker_value:
                            agents.add(virus)

                if pcr_result == detectable_value and not agents:
                    agents.add("Detectável sem agente codificado")
                    detectable_without_agent += 1

                if len(agents) > 1:
                    records_with_multiple_agents += 1

                for agent in agents:
                    weekly_detections[(week, agent)] += 1
                    municipal_detections[(code, week, agent)] += 1
                    total_agent_detections += 1

    finally:
        reader.close()
    weekly_rows = []
    all_weeks = sorted(weekly_totals)
    all_agents = sorted({agent for _, agent in weekly_detections})
    for week in all_weeks:
        total = weekly_totals[week]
        registrations = int(total["registros"])
        available = int(total["pcr_resultado_disponivel"])
        conclusive = int(total["pcr_conclusivo"])
        inconclusive = int(total["pcr_inconclusivo"])
        detectable = int(total["pcr_detectavel"])
        for agent in all_agents:
            detections = int(weekly_detections.get((week, agent), 0))
            weekly_rows.append({
                "SE": week,
                "virus": agent,
                "deteccoes": detections,
                "registros_srag": registrations,
                "pcr_resultado_disponivel": available,
                "pcr_conclusivo": conclusive,
                "pcr_inconclusivo": inconclusive,
                "pcr_detectavel": detectable,
                "cobertura_resultado_molecular_percent": (
                    available / registrations * 100.0 if registrations else None
                ),
                "cobertura_resultado_conclusivo_percent": (
                    conclusive / registrations * 100.0 if registrations else None
                ),
                "participacao_entre_deteccoes_percent": None,
            })

        weekly_detection_total = sum(
            int(weekly_detections.get((week, agent), 0))
            for agent in all_agents
        )
        if weekly_detection_total:
            for row in weekly_rows:
                if row["SE"] == week:
                    row["participacao_entre_deteccoes_percent"] = (
                        row["deteccoes"] / weekly_detection_total * 100.0
                    )

    municipal_rows = []
    for (code, week), total in sorted(municipal_totals.items()):
        ref_row = ref_by6.loc[code]
        agents = sorted({
            virus for (mun, se, virus), value in municipal_detections.items()
            if mun == code and se == week and value > 0
        })
        if not agents:
            agents = ["Sem agente detectado/codificado"]

        detection_total = sum(
            int(municipal_detections.get((code, week, agent), 0))
            for agent in agents
        )
        registrations = int(total["registros"])
        available = int(total["pcr_resultado_disponivel"])
        conclusive = int(total["pcr_conclusivo"])
        inconclusive = int(total["pcr_inconclusivo"])
        detectable = int(total["pcr_detectavel"])

        for agent in agents:
            detections = int(municipal_detections.get((code, week, agent), 0))
            municipal_rows.append({
                "codigo_ibge": ref_row["codigo_ibge"],
                "municipio": ref_row["municipio"],
                "SE": week,
                "virus": agent,
                "deteccoes": detections,
                "registros_srag": registrations,
                "pcr_resultado_disponivel": available,
                "pcr_conclusivo": conclusive,
                "pcr_inconclusivo": inconclusive,
                "pcr_detectavel": detectable,
                "cobertura_resultado_molecular_percent": (
                    available / registrations * 100.0 if registrations else None
                ),
                "cobertura_resultado_conclusivo_percent": (
                    conclusive / registrations * 100.0 if registrations else None
                ),
                "participacao_entre_deteccoes_percent": (
                    detections / detection_total * 100.0 if detection_total else None
                ),
            })

    weekly = pd.DataFrame(weekly_rows)
    municipal = pd.DataFrame(municipal_rows)

    metadata = {
        "dimension": "virology",
        "reference_year": year,
        "mt_records_seen": int(mt_rows),
        "invalid_municipality_rows": int(invalid_municipality),
        "invalid_week_rows": int(invalid_week),
        "agent_detections": int(total_agent_detections),
        "records_with_multiple_agents": int(records_with_multiple_agents),
        "detectable_without_agent": int(detectable_without_agent),
        "specific_virus_positivity_enabled": False,
        "coinfection_allowed": True,
        "denominator_note": (
            "Ausência de marcador específico não comprova teste daquele agente. "
            "A saída separa resultado molecular disponível, conclusivo e inconclusivo, além de detecções; "
            "não usa positividade específica por vírus sem denominador validado."
        ),
    }
    return weekly, municipal, metadata
