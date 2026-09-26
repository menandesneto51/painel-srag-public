# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


WEEKLY_ALIASES = {
    "hospitalizacoes": "hospitalizados",
    "taxa_uti_hosp_percent": "tx_uti_percent",
}


def issue(severity: str, scope: str, code: str, message: str) -> dict[str, str]:
    return {
        "severity": severity,
        "scope": scope,
        "code": code,
        "message": message,
    }


def weekly_value(record: dict[str, Any] | None, key: str) -> Any:
    if not record:
        return None
    if key in record:
        return record.get(key)
    alias = WEEKLY_ALIASES.get(key)
    return record.get(alias) if alias else None


def _numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def validate_loaded_data(
    metadata: dict[str, Any],
    kpis: dict[str, Any],
    weekly: pd.DataFrame,
    risk: pd.DataFrame,
    forecast: pd.DataFrame,
    or_obito: pd.DataFrame,
    or_uti: pd.DataFrame,
    risk_candidate: pd.DataFrame | None = None,
) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []

    # --- Temporal / metadata ---
    if weekly.empty:
        issues.append(issue("error", "temporal", "WEEKLY_EMPTY", "weekly_summary.csv está vazio."))
    else:
        if "SE_NOTIF" not in weekly.columns:
            issues.append(issue("error", "temporal", "SE_COLUMN_MISSING", "Coluna SE_NOTIF ausente no resumo semanal."))
        else:
            se = _numeric(weekly["SE_NOTIF"]).dropna()
            if not se.empty:
                max_se = int(se.max())
                stable_week = metadata.get("stable_week")
                try:
                    stable_week_int = int(stable_week)
                    if not 1 <= stable_week_int <= 53:
                        issues.append(issue("error", "temporal", "STABLE_WEEK_RANGE", f"stable_week={stable_week_int} fora do intervalo 1..53."))
                    if stable_week_int > max_se:
                        issues.append(issue(
                            "error",
                            "temporal",
                            "STABLE_WEEK_AFTER_DATA",
                            f"stable_week={stable_week_int} é superior à maior SE observada ({max_se}).",
                        ))
                except (TypeError, ValueError):
                    issues.append(issue("error", "temporal", "STABLE_WEEK_INVALID", "stable_week ausente ou inválida."))

        if "ANO_NOTIF" in weekly.columns and metadata.get("year") is not None:
            years = set(_numeric(weekly["ANO_NOTIF"]).dropna().astype(int).tolist())
            try:
                meta_year = int(metadata["year"])
                if years and meta_year not in years:
                    issues.append(issue("error", "temporal", "YEAR_MISMATCH", f"Ano do metadata ({meta_year}) não aparece no resumo semanal."))
            except (TypeError, ValueError):
                issues.append(issue("error", "temporal", "YEAR_INVALID", "Ano de referência do metadata é inválido."))

    generated_at = metadata.get("generated_at")
    if generated_at:
        try:
            generated = pd.Timestamp(generated_at)
            age_days = (pd.Timestamp.now(tz=None) - generated.tz_localize(None) if generated.tzinfo else pd.Timestamp.now() - generated).days
            if age_days > 21:
                issues.append(issue(
                    "warning",
                    "temporal",
                    "SNAPSHOT_STALE",
                    f"Snapshot gerado há {age_days} dias; conferir atualização do banco vivo antes de interpretar tendência atual.",
                ))
        except Exception:
            issues.append(issue("warning", "temporal", "GENERATED_AT_INVALID", "generated_at não pôde ser interpretado."))

    # --- KPI contract ---
    weekly_ref = kpis.get("weekly_reference", {})
    weekly_prev = kpis.get("weekly_previous", {})
    if weekly_ref and "SE_NOTIF" in weekly_ref and not weekly.empty and "SE_NOTIF" in weekly.columns:
        available = set(_numeric(weekly["SE_NOTIF"]).dropna().astype(int).tolist())
        try:
            if int(weekly_ref["SE_NOTIF"]) not in available:
                issues.append(issue("error", "kpi", "REFERENCE_WEEK_NOT_FOUND", "A SE de weekly_reference não existe no resumo semanal."))
        except (TypeError, ValueError):
            issues.append(issue("error", "kpi", "REFERENCE_WEEK_INVALID", "SE de weekly_reference inválida."))

    if weekly_prev and "SE_NOTIF" in weekly_prev and not weekly.empty and "SE_NOTIF" in weekly.columns:
        available = set(_numeric(weekly["SE_NOTIF"]).dropna().astype(int).tolist())
        try:
            if int(weekly_prev["SE_NOTIF"]) not in available:
                issues.append(issue("error", "kpi", "PREVIOUS_WEEK_NOT_FOUND", "A SE de weekly_previous não existe no resumo semanal."))
        except (TypeError, ValueError):
            issues.append(issue("error", "kpi", "PREVIOUS_WEEK_INVALID", "SE de weekly_previous inválida."))

    # --- Risk / denominators ---
    if not risk.empty:
        code_cols = {"CD_MUN", "codigo_ibge", "cod_ibge", "codigo_municipio"}
        pop_cols = {"populacao", "populacao_ibge", "populacao_2026"}
        if not code_cols.intersection(risk.columns):
            issues.append(issue(
                "error",
                "risk",
                "MUNICIPAL_CODE_MISSING",
                "risk_summary.csv não contém código IBGE municipal auditável.",
            ))
        if not pop_cols.intersection(risk.columns):
            issues.append(issue(
                "error",
                "risk",
                "POPULATION_MISSING",
                "risk_summary.csv não contém o denominador populacional usado para calcular incidência.",
            ))

        for col in ("incidencia_100k", "incidencia_recente_100k"):
            if col in risk.columns:
                vals = _numeric(risk[col])
                if (vals.dropna() < 0).any():
                    issues.append(issue("error", "risk", "NEGATIVE_INCIDENCE", f"{col} contém valores negativos."))
                if (vals.dropna() > 10000).any():
                    issues.append(issue(
                        "warning",
                        "risk",
                        "EXTREME_INCIDENCE",
                        f"{col} contém valores superiores a 10.000/100 mil; revisar numerador e denominador.",
                    ))

        for col in ("tx_uti_percent", "letalidade_percent", "score_risco_srag"):
            if col in risk.columns:
                vals = _numeric(risk[col]).dropna()
                if ((vals < 0) | (vals > 100)).any():
                    issues.append(issue("error", "risk", "PERCENT_RANGE", f"{col} possui valor fora de 0..100."))

    # --- Audited v2 territorial candidate ---
    if risk_candidate is not None:
        required_candidate = {
            "codigo_ibge",
            "NM_MUN",
            "populacao",
            "notificacoes",
            "casos_recentes",
            "incidencia_100k",
            "incidencia_recente_100k",
            "score_v2_status",
        }
        missing_candidate = required_candidate.difference(risk_candidate.columns)
        if missing_candidate:
            issues.append(issue(
                "error",
                "risk_candidate",
                "SCHEMA_MISSING",
                "Artefato territorial v2 sem colunas obrigatórias: " + ", ".join(sorted(missing_candidate)),
            ))
        else:
            rc = risk_candidate.copy()
            if len(rc) != 142:
                issues.append(issue(
                    "error",
                    "risk_candidate",
                    "MUNICIPAL_COUNT",
                    f"Artefato territorial v2 deve conter 142 municípios; encontrados {len(rc)}.",
                ))

            codes = rc["codigo_ibge"].astype("string").str.replace(r"\\.0$", "", regex=True).str.zfill(7)
            if codes.duplicated().any():
                issues.append(issue("error", "risk_candidate", "DUPLICATE_IBGE", "Há códigos IBGE duplicados."))
            if not codes.str.match(r"^51\\d{5}$", na=False).all():
                issues.append(issue("error", "risk_candidate", "INVALID_IBGE", "Há código IBGE inválido ou fora de Mato Grosso."))

            population = _numeric(rc["populacao"])
            if population.isna().any() or (population <= 0).any():
                issues.append(issue("error", "risk_candidate", "INVALID_POPULATION", "Há população municipal ausente ou não positiva."))
            elif int(round(population.sum())) != 3_950_330:
                issues.append(issue(
                    "error",
                    "risk_candidate",
                    "STATE_POPULATION_MISMATCH",
                    f"Soma populacional={int(round(population.sum()))}; esperado=3.950.330 para a referência IBGE 2026 versionada.",
                ))

            notifications = _numeric(rc["notificacoes"])
            recent = _numeric(rc["casos_recentes"])
            incidence = _numeric(rc["incidencia_100k"])
            recent_incidence = _numeric(rc["incidencia_recente_100k"])

            expected_incidence = notifications / population * 100000.0
            expected_recent = recent / population * 100000.0

            mismatch = (incidence - expected_incidence).abs() > 1e-4
            recent_mismatch = (recent_incidence - expected_recent).abs() > 1e-4
            if mismatch.fillna(True).any():
                issues.append(issue(
                    "error",
                    "risk_candidate",
                    "INCIDENCE_NOT_REPRODUCIBLE",
                    "incidencia_100k não é reproduzível a partir de notificacoes/populacao em todas as linhas.",
                ))
            if recent_mismatch.fillna(True).any():
                issues.append(issue(
                    "error",
                    "risk_candidate",
                    "RECENT_INCIDENCE_NOT_REPRODUCIBLE",
                    "incidencia_recente_100k não é reproduzível a partir de casos_recentes/populacao em todas as linhas.",
                ))

            statuses = set(rc["score_v2_status"].astype("string").str.lower().dropna().tolist())
            if not statuses.issubset({"blocked", "under_calibration", "experimental"}):
                issues.append(issue(
                    "error",
                    "risk_candidate",
                    "UNAPPROVED_SCORE_STATUS",
                    "score_v2_status contém estado não autorizado antes da calibração/backtesting.",
                ))

    # --- Forecast ---
    if not forecast.empty:
        required = {"valor_esperado", "ic95_inf", "ic95_sup"}
        if required.issubset(forecast.columns):
            expected = _numeric(forecast["valor_esperado"])
            low = _numeric(forecast["ic95_inf"])
            high = _numeric(forecast["ic95_sup"])
            invalid = (low > expected) | (expected > high) | (low > high)
            if invalid.fillna(False).any():
                issues.append(issue("error", "forecast", "FORECAST_INTERVAL_INVALID", "Forecast possui estimativa fora do IC95% ou limites invertidos."))

    # --- OR ---
    for scope, table in (("or_obito", or_obito), ("or_uti", or_uti)):
        required = {"OR", "IC95% inferior", "IC95% superior"}
        if not table.empty and required.issubset(table.columns):
            estimate = _numeric(table["OR"])
            low = _numeric(table["IC95% inferior"])
            high = _numeric(table["IC95% superior"])
            invalid = (low > estimate) | (estimate > high) | (low > high)
            if invalid.fillna(False).any():
                issues.append(issue("error", scope, "OR_INTERVAL_INVALID", f"{scope} possui OR fora do IC95% ou limites invertidos."))

    publication_status = str(metadata.get("publication_status", "")).lower().strip()
    if publication_status in {"blocked", "under_review"}:
        issues.append(issue(
            "warning",
            "publication",
            "PUBLICATION_NOT_VALIDATED",
            f"Metadata informa publication_status='{publication_status}'.",
        ))

    return issues


def has_errors(issues: list[dict[str, str]], scopes: set[str] | None = None) -> bool:
    for item in issues:
        if item["severity"] != "error":
            continue
        if scopes is None or item["scope"] in scopes:
            return True
    return False


def find_public_file(root: Path, filename: str) -> Path:
    for candidate in (root / "data_public" / filename, root / filename):
        if candidate.exists():
            return candidate
    return root / "data_public" / filename


def load_snapshot(root: Path) -> dict[str, Any]:
    import json

    def read_json(name: str) -> dict[str, Any]:
        return json.loads(find_public_file(root, name).read_text(encoding="utf-8-sig"))

    def read_csv(name: str) -> pd.DataFrame:
        return pd.read_csv(find_public_file(root, name), encoding="utf-8-sig")

    return {
        "metadata": read_json("metadata_public.json"),
        "kpis": read_json("kpis.json"),
        "weekly": read_csv("weekly_summary.csv"),
        "risk": read_csv("risk_summary.csv"),
        "forecast": read_csv("forecast_summary.csv"),
        "or_obito": read_csv("or_obito_summary.csv"),
        "or_uti": read_csv("or_uti_summary.csv"),
        "risk_candidate": (
            read_csv("risk_summary_v2_candidate.csv")
            if find_public_file(root, "risk_summary_v2_candidate.csv").exists()
            else None
        ),
    }


def validate_snapshot(root: Path) -> list[dict[str, str]]:
    data = load_snapshot(root)
    return validate_loaded_data(**data)
