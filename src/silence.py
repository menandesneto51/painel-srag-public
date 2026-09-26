# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


VALID_REPORTING_EVIDENCE = {
    "explicit_zero_report",
    "recent_reporting_activity",
    "none",
    "unknown",
}


def classify_silence(
    *,
    observed_cases: int,
    baseline_median: float | None,
    baseline_q75: float | None,
    baseline_n_years: int,
    reporting_evidence: str,
    data_quality_class: str | None,
    regional_signal_status: str | None,
    min_baseline_years: int = 3,
    priority_expected_median: float = 2.0,
    regional_priority_signals: set[str] | None = None,
) -> dict[str, Any]:
    if observed_cases < 0:
        raise ValueError("observed_cases não pode ser negativo.")
    if reporting_evidence not in VALID_REPORTING_EVIDENCE:
        raise ValueError(f"reporting_evidence inválido: {reporting_evidence}")

    regional_priority_signals = regional_priority_signals or {"persistent_elevated"}

    if observed_cases > 0:
        return {
            "silence_class": "not_silent",
            "reason": "Há casos observados na janela atual.",
            "priority_candidate": False,
            "model_status": "experimental",
        }

    if baseline_n_years < min_baseline_years or baseline_median is None or baseline_q75 is None:
        return {
            "silence_class": "insufficient_baseline",
            "reason": "Baseline histórico insuficiente para interpretar zero observado.",
            "priority_candidate": False,
            "model_status": "experimental",
        }

    baseline_median = float(baseline_median)
    baseline_q75 = float(baseline_q75)

    if baseline_median <= 0 and baseline_q75 <= 0:
        return {
            "silence_class": "absence_compatible_with_expected",
            "reason": "Zero observado é compatível com histórico sem atividade esperada na janela.",
            "priority_candidate": False,
            "model_status": "experimental",
        }

    quality_weak = data_quality_class in {None, "low", "insufficient"}
    has_reporting_evidence = reporting_evidence in {
        "explicit_zero_report",
        "recent_reporting_activity",
    }

    if not has_reporting_evidence and quality_weak:
        return {
            "silence_class": "data_quality_or_reporting_gap",
            "reason": (
                "Há atividade histórica esperada, mas faltam evidências suficientes de "
                "funcionamento/qualidade da notificação na janela."
            ),
            "priority_candidate": False,
            "model_status": "experimental",
        }

    priority = bool(
        baseline_median >= float(priority_expected_median)
        and regional_signal_status in regional_priority_signals
        and has_reporting_evidence
        and not quality_weak
    )

    if priority:
        return {
            "silence_class": "silence_priority_candidate",
            "reason": (
                "Zero observado apesar de atividade histórica esperada, evidência de notificação "
                "e sinal regional persistente."
            ),
            "priority_candidate": True,
            "model_status": "experimental",
        }

    return {
        "silence_class": "silence_under_investigation",
        "reason": (
            "Zero observado apesar de atividade histórica esperada; requer verificação "
            "antes de concluir ausência de transmissão/doença."
        ),
        "priority_candidate": False,
        "model_status": "experimental",
    }


def derive_reporting_evidence(
    *,
    explicit_zero_report: bool = False,
    prior_window_records: int | None = None,
) -> str:
    if explicit_zero_report:
        return "explicit_zero_report"
    if prior_window_records is None:
        return "unknown"
    if prior_window_records > 0:
        return "recent_reporting_activity"
    return "none"


def load_silence_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))
