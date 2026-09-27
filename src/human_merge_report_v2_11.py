# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd


def summarize_human_merge_cycle(
    decisions: pd.DataFrame,
    post_merge: pd.DataFrame | None = None,
) -> dict:
    required_decisions = {
        "merge_decision_record_id",
        "merge_decision",
        "merge_decision_is_not_merge_execution",
        "automatic_merge_enabled",
        "automatic_deploy_enabled",
        "automatic_rollback_enabled",
        "human_merge_required",
    }
    missing = required_decisions.difference(decisions.columns)
    if missing:
        raise ValueError(f"Decisões v2.11 sem colunas: {sorted(missing)}")

    if not decisions["merge_decision_is_not_merge_execution"].astype(bool).all():
        raise ValueError("Decisão humana deve permanecer distinta de merge executado.")
    if decisions["automatic_merge_enabled"].astype(bool).any():
        raise ValueError("Merge automático não é permitido.")
    if decisions["automatic_deploy_enabled"].astype(bool).any():
        raise ValueError("Deploy automático não é permitido.")
    if decisions["automatic_rollback_enabled"].astype(bool).any():
        raise ValueError("Rollback automático não é permitido.")
    if not decisions["human_merge_required"].astype(bool).all():
        raise ValueError("Merge humano deve permanecer obrigatório.")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "merge_decisions": int(len(decisions)),
        "merge_decisions_by_status": {
            str(k): int(v)
            for k, v in decisions["merge_decision"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        },
        "merge_decision_is_not_merge_execution": True,
        "automatic_merge": False,
        "automatic_deploy": False,
        "automatic_rollback": False,
        "human_merge_required": True,
    }

    if post_merge is not None and not post_merge.empty:
        required_post = {
            "post_merge_record_id",
            "post_merge_state",
            "rollback_readiness_status",
            "post_merge_record_requires_actual_merge_evidence",
            "post_merge_record_is_not_deploy",
            "automatic_deploy_enabled",
            "automatic_rollback_enabled",
            "human_post_merge_verification_required",
        }
        missing_post = required_post.difference(post_merge.columns)
        if missing_post:
            raise ValueError(
                f"Registros pós-merge sem colunas: {sorted(missing_post)}"
            )
        if not post_merge[
            "post_merge_record_requires_actual_merge_evidence"
        ].astype(bool).all():
            raise ValueError("Pós-merge deve exigir evidência real de merge.")
        if not post_merge["post_merge_record_is_not_deploy"].astype(bool).all():
            raise ValueError("Registro pós-merge deve permanecer distinto de deploy.")
        if post_merge["automatic_deploy_enabled"].astype(bool).any():
            raise ValueError("Deploy automático não é permitido.")
        if post_merge["automatic_rollback_enabled"].astype(bool).any():
            raise ValueError("Rollback automático não é permitido.")
        if not post_merge[
            "human_post_merge_verification_required"
        ].astype(bool).all():
            raise ValueError("Verificação humana pós-merge deve ser obrigatória.")

        summary["post_merge_records"] = int(len(post_merge))
        summary["post_merge_states"] = {
            str(k): int(v)
            for k, v in post_merge["post_merge_state"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        }
        summary["rollback_readiness"] = {
            str(k): int(v)
            for k, v in post_merge["rollback_readiness_status"]
            .astype("string")
            .value_counts(dropna=False)
            .to_dict()
            .items()
        }

    return summary


def render_human_merge_cycle_report(
    decisions: pd.DataFrame,
    post_merge: pd.DataFrame | None = None,
) -> str:
    summary = summarize_human_merge_cycle(decisions, post_merge)

    lines = [
        "# Decisão Humana de Merge e Verificação Pós-Merge — v2.11",
        "",
        "> Decisão de merge não é execução do merge. Registro pós-merge não é deploy.",
        "",
        f"- Decisões de merge: **{summary['merge_decisions']}**",
        "- Merge automático: **desabilitado**",
        "- Deploy automático: **desabilitado**",
        "- Rollback automático: **desabilitado**",
        "- Merge humano: **obrigatório**",
        "",
        "## Decisões humanas",
        "",
    ]
    for key, value in sorted(summary["merge_decisions_by_status"].items()):
        lines.append(f"- **{key}**: {value}")

    if "post_merge_records" in summary:
        lines += [
            "",
            "## Verificação pós-merge",
            "",
            f"- Registros pós-merge: **{summary['post_merge_records']}**",
        ]
        for key, value in sorted(summary["post_merge_states"].items()):
            lines.append(f"- Estado **{key}**: {value}")

        lines += ["", "### Rollback readiness", ""]
        for key, value in sorted(summary["rollback_readiness"].items()):
            lines.append(f"- **{key}**: {value}")

    lines += [
        "",
        "## Governança",
        "",
        "- approve_human_merge registra aprovação humana; não prova que o merge ocorreu.",
        "- Registro pós-merge exige merge_evidence_ref e merged_commit_sha.",
        "- verified_healthy exige verificações aprovadas e rollback readiness = ready.",
        "- Nenhum registro v2.11 executa deploy ou rollback automaticamente.",
        "",
    ]
    return "\n".join(lines)
