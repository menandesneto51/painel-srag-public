# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from src.human_workflow_concordance_v2_6 import summarize_concordance


def render_concordance_report(concordance: pd.DataFrame) -> str:
    summary = summarize_concordance(concordance)
    lines = [
        "# Concordância entre Workflow e Decisão Humana — v2.6",
        "",
        "> Este relatório avalia regras do sistema. Não avalia desempenho individual do revisor e não usa decisão humana como padrão-ouro epidemiológico.",
        "",
        f"- Decisões avaliadas: **{summary['decision_records']}**",
        f"- Registros que exigem revisão de regra: **{summary['rule_review_records']}**",
        "- Reviewer scoring: **desabilitado**",
        "- Ranking municipal: **desabilitado**",
        "- Alteração automática de regra: **desabilitada**",
        "",
        "## Concordância por classe",
        "",
    ]
    for key, value in sorted(summary["alignment_counts"].items()):
        lines.append(f"- **{key}**: {value}")

    lines += ["", "## Filas com registros para revisão de regra", ""]
    if summary["rule_review_by_queue"]:
        for key, value in sorted(summary["rule_review_by_queue"].items()):
            lines.append(f"- **{key}**: {value}")
    else:
        lines.append("Nenhum registro.")

    lines += [
        "",
        "## Interpretação",
        "",
        "- routine_escalated_rule_review: uma fila de rotina terminou em decisão humana de escalonamento; revisar se faltou gatilho/contexto.",
        "- nonroutine_not_escalated_rule_review: uma fila não rotineira terminou sem escalonamento; revisar se a regra foi excessivamente sensível ou se havia contexto não modelado.",
        "- Discordância não significa erro humano.",
        "- Concordância não prova correção epidemiológica da regra.",
        "",
        "## Governança",
        "",
        "Qualquer alteração de regra exige análise de casos, documentação, teste retrospectivo e aprovação humana. Nenhuma regra é reescrita automaticamente.",
        "",
    ]
    return "\n".join(lines)


def build_concordance_metadata(concordance: pd.DataFrame) -> dict:
    summary = summarize_concordance(concordance)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        **summary,
        "human_decision_is_epidemiological_gold_standard": False,
        "reviewer_scoring": False,
        "municipality_ranking": False,
        "automatic_rule_change": False,
        "automatic_execution": False,
        "status": "experimental_rule_governance",
    }
