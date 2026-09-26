# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class Signal:
    value: float | None
    status: str
    note: str = ""


def rate_per_100k(events: float | int | None, population: float | int | None) -> Signal:
    if events is None or population is None:
        return Signal(None, "insufficient", "numerador ou população ausente")
    events = float(events)
    population = float(population)
    if not isfinite(events) or not isfinite(population) or population <= 0 or events < 0:
        return Signal(None, "invalid", "numerador/população inválido")
    return Signal(events / population * 100000.0, "ok")


def smoothed_proportion(
    events: float | int | None,
    denominator: float | int | None,
    statewide_rate: float | None,
    prior_strength: float,
) -> Signal:
    if events is None or denominator is None or statewide_rate is None:
        return Signal(None, "insufficient", "parâmetros insuficientes")
    events = float(events)
    denominator = float(denominator)
    statewide_rate = float(statewide_rate)
    prior_strength = float(prior_strength)

    if denominator < 0 or events < 0 or events > denominator:
        return Signal(None, "invalid", "eventos incompatíveis com denominador")
    if not (0 <= statewide_rate <= 1):
        return Signal(None, "invalid", "taxa estadual deve estar entre 0 e 1")
    if prior_strength <= 0:
        return Signal(None, "invalid", "prior_strength deve ser positivo")

    value = (events + prior_strength * statewide_rate) / (denominator + prior_strength)
    note = "estimativa suavizada; prior_strength deve ser calibrado por backtesting"
    return Signal(value, "experimental", note)


def trend_ratio(
    recent_mean: float | None,
    previous_mean: float | None,
    pseudocount: float = 0.5,
) -> Signal:
    if recent_mean is None or previous_mean is None:
        return Signal(None, "insufficient", "janelas temporais ausentes")
    recent_mean = float(recent_mean)
    previous_mean = float(previous_mean)
    if recent_mean < 0 or previous_mean < 0 or pseudocount <= 0:
        return Signal(None, "invalid", "parâmetros inválidos")
    value = (recent_mean + pseudocount) / (previous_mean + pseudocount)
    return Signal(value, "experimental", "usar somente em semanas temporalmente comparáveis")


def publication_ready(model_status: str, backtesting_ok: bool, denominators_ok: bool) -> bool:
    return model_status == "validated" and bool(backtesting_ok) and bool(denominators_ok)
