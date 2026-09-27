# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, timedelta


def epidemiological_week1_start(year: int) -> date:
    """Calendário epidemiológico: semana começa domingo; SE1 contém 4 de janeiro."""
    jan4 = date(int(year), 1, 4)
    days_since_sunday = (jan4.weekday() + 1) % 7
    return jan4 - timedelta(days=days_since_sunday)


def epidemiological_week_start(year: int, week: int) -> date:
    year = int(year)
    week = int(week)
    if week < 1:
        raise ValueError("Semana epidemiológica deve ser >= 1.")

    start = epidemiological_week1_start(year) + timedelta(weeks=week - 1)
    next_year_start = epidemiological_week1_start(year + 1)
    if start >= next_year_start:
        raise ValueError(f"Semana epidemiológica {week} não existe em {year}.")
    return start


def epidemiological_week_end(year: int, week: int) -> date:
    return epidemiological_week_start(year, week) + timedelta(days=6)


def epidemiological_weeks_in_year(year: int) -> int:
    """Retorna 52 ou 53 semanas epidemiológicas válidas no ano."""
    year = int(year)
    count = 0
    for week in range(1, 54):
        try:
            epidemiological_week_start(year, week)
        except ValueError:
            break
        count = week
    if count not in {52, 53}:
        raise ValueError(f"Calendário epidemiológico inesperado para {year}: {count} semanas.")
    return count
