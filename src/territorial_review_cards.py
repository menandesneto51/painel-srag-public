# -*- coding: utf-8 -*-
from __future__ import annotations

import pandas as pd


def _text(value: object) -> str:
    if value is None or pd.isna(value):
        return ""
    return str(value).strip()


def build_review_cards(territorial: pd.DataFrame) -> pd.DataFrame:
    required = {
        "codigo_ibge",
        "municipio",
        "signal_status",
        "signal_confidence",
        "silence_status",
        "virology_status",
        "healthcare_pressure_available",
        "territorial_model_status",
    }
    missing = required.difference(territorial.columns)
    if missing:
        raise ValueError(
            f"Inteligência territorial sem colunas obrigatórias: {sorted(missing)}"
        )

    rows = []
    for row in territorial.itertuples(index=False):
        data = row._asdict()
        tags: list[str] = []
        evidence: list[str] = []
        review_notes: list[str] = []

        signal = _text(data.get("signal_status"))
        confidence = _text(data.get("signal_confidence"))
        silence = _text(data.get("silence_status"))
        virology_status = _text(data.get("virology_status"))
        dominant = _text(data.get("virology_dominant_agent"))
        pressure_available = bool(data.get("healthcare_pressure_available", False))
        pressure_status = _text(data.get("pressure_status"))
        pressure_validation = _text(data.get("validation_status"))

        if signal == "elevated_and_rising_experimental":
            tags.append("epidemiology_review")
            evidence.append("atividade acima do esperado com tendência crescente")
        elif signal == "elevated_not_rising_experimental":
            tags.append("epidemiology_review")
            evidence.append("atividade acima do esperado sem tendência crescente")
        elif signal == "rising_without_baseline_excess_experimental":
            tags.append("trend_review")
            evidence.append("tendência crescente sem excesso frente ao baseline")

        if confidence == "low_experimental":
            tags.append("data_quality_review")
            evidence.append("baixa confiança no sinal")
            review_notes.append(
                "Priorizar revisão de oportunidade, completude e inconsistências antes de interpretar o sinal."
            )
        elif confidence == "insufficient":
            tags.append("insufficient_evidence")
            evidence.append("confiança insuficiente")
            review_notes.append(
                "Não interpretar ausência ou excesso como evidência operacional sem revisão dos dados."
            )

        if silence == "silence_signal_under_review":
            tags.append("silence_verification")
            evidence.append("silêncio inesperado em contexto historicamente ativo")
            review_notes.append(
                "Verificar fluxo de notificação e oportunidade antes de concluir ausência de atividade."
            )
        elif silence == "zero_observed_low_confidence":
            tags.append("data_quality_review")
            evidence.append("zero observado com baixa confiança")

        if virology_status == "named_agent_detected":
            tags.append("virology_review")
            if dominant:
                evidence.append(f"agente predominante detectado: {dominant}")
        elif virology_status == "detectable_without_named_agent":
            tags.append("virology_review")
            evidence.append("resultado detectável sem agente codificado")
            review_notes.append(
                "Revisar codificação laboratorial/virológica antes de interpretar composição viral."
            )
        elif virology_status == "no_molecular_result_available":
            tags.append("laboratory_coverage_review")
            evidence.append("sem resultado molecular disponível na janela")

        if pressure_available:
            tags.append("healthcare_coordination")
            if pressure_status:
                evidence.append(f"pressão assistencial informada: {pressure_status}")
            if pressure_validation != "validated":
                review_notes.append(
                    "A dimensão assistencial existe, mas ainda não está validada para interpretação operacional."
                )

        # Preserve deterministic order while removing duplicates.
        tags = list(dict.fromkeys(tags))
        evidence = list(dict.fromkeys(evidence))
        review_notes = list(dict.fromkeys(review_notes))

        if evidence:
            summary = "; ".join(evidence) + "."
        else:
            summary = (
                "Nenhum sinal multidimensional específico exige destaque automático "
                "pelas regras experimentais atuais."
            )

        rows.append({
            "codigo_ibge": _text(data.get("codigo_ibge")),
            "municipio": _text(data.get("municipio")),
            "review_tags": "|".join(tags),
            "evidence_summary": summary,
            "review_notes": " ".join(review_notes),
            "human_review_required": True,
            "operational_recommendation_enabled": False,
            "composite_score_used": False,
            "card_status": "experimental_explainable_review",
        })

    return pd.DataFrame(rows).sort_values("codigo_ibge").reset_index(drop=True)
