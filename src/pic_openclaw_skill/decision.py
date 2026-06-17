"""Decision construction helpers."""

from __future__ import annotations

from uuid import uuid4

from pic_openclaw_skill.records import (
    BridgeDecision,
    DecisionName,
    InputRecord,
    PicDiagnostics,
    PolicyMode,
)
from pic_openclaw_skill.safety import SAFETY_BOUNDARY, safe_ref, sanitize_public_text


def make_decision(
    record: InputRecord,
    *,
    input_ref: str,
    mode: PolicyMode = "advisory",
    decision: DecisionName,
    reasons: list[str],
    missing_obligations: list[str] | None = None,
    residual_summary: dict[str, float] | None = None,
    pic_used: bool = False,
    pic_accepted: bool | None = None,
    pic_operationally_usable: bool | None = None,
    pic_settled: bool | None = None,
    pic_diagnostics: PicDiagnostics | None = None,
    safe_next_steps: list[str] | None = None,
) -> BridgeDecision:
    allowed = mode != "observe" and decision == "allow"
    policy_allows_next_step = mode != "observe" and decision in {"allow", "warn"}
    requires_user_authorization = _requires_user_authorization(record, decision)
    return BridgeDecision(
        decision_id=f"bridge-decision:{uuid4()}",
        input_ref=safe_ref(input_ref),
        phase=record.phase,
        mode=mode,
        decision=decision,
        allowed_to_execute=allowed,
        policy_allows_next_step=policy_allows_next_step,
        requires_human_review=decision in {"defer", "block"} or _requires_review(record),
        requires_user_authorization=requires_user_authorization,
        pic_used=pic_used,
        pic_accepted=pic_accepted,
        pic_operationally_usable=pic_operationally_usable,
        pic_settled=pic_settled,
        missing_obligations=sorted(
            {sanitize_public_text(item) for item in missing_obligations or []}
        ),
        residual_summary=dict(sorted((residual_summary or {}).items())),
        pic_diagnostics=_sanitize_pic_diagnostics(pic_diagnostics),
        safe_next_steps=safe_next_steps or default_safe_next_steps(decision),
        reasons=sorted({sanitize_public_text(item) for item in reasons}),
        safety_boundary=SAFETY_BOUNDARY,
    )


def default_safe_next_steps(decision: DecisionName) -> list[str]:
    steps = [
        "attach evidence",
        "add rollback plan",
        "ask for explicit human confirmation",
        "reduce action scope",
        "rerun the check",
    ]
    if decision == "block":
        return ["do not execute the proposed action", *steps]
    if decision == "allow":
        return ["execute only after normal OpenClaw user approval and policy checks"]
    return steps


def _requires_review(record: InputRecord) -> bool:
    return bool(getattr(record, "requires_human_confirmation", False)) or getattr(
        record, "risk_level", "low"
    ) in {"high", "critical"}


def _requires_user_authorization(record: InputRecord, decision: DecisionName) -> bool:
    return (
        decision in {"defer", "block"}
        or _requires_review(record)
        or bool(getattr(record, "external_effect", False))
    )


def _sanitize_pic_diagnostics(diagnostics: PicDiagnostics | None) -> PicDiagnostics:
    if diagnostics is None:
        return PicDiagnostics()
    return PicDiagnostics(
        agent_tasks=_sanitize_text_list(diagnostics.agent_tasks),
        route_execution_requests=_sanitize_text_list(diagnostics.route_execution_requests),
        residual_ledger=_sanitize_text_list(diagnostics.residual_ledger),
        provenance_refs=_sanitize_text_list(diagnostics.provenance_refs),
    )


def _sanitize_text_list(items: list[str]) -> list[str]:
    return [sanitize_public_text(item) for item in items]
