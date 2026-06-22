"""Deterministic OpenClaw bridge policy."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping

from pic_openclaw_skill.decision import make_decision
from pic_openclaw_skill.records import (
    BridgeDecision,
    DecisionName,
    InputRecord,
    OpenClawActionProposal,
    OpenClawMemoryWrite,
    OpenClawResultClaim,
    OpenClawSkillInstall,
    PicDiagnostics,
    PolicyMode,
)
from pic_openclaw_skill.safety import sanitize_public_text

DESTRUCTIVE_ACTION_KINDS = {
    "file_delete",
    "delete_file",
    "repository_mutation",
    "repo_mutation",
    "payment",
    "purchase",
    "irreversible_transaction",
}

SHELL_ACTION_KINDS = {"shell", "shell_command", "command", "terminal"}
NETWORK_ACTION_KINDS = {"network_request", "http_request", "web_request"}
CREDENTIAL_WORDS = {"credential", "credentials", "token", "secret", "password", "private_key"}
UNCLEAR_PERMISSIONS = {"*", "all", "admin", "unknown", "full-access", "full_access"}
PIC_DIAGNOSTIC_ITEM_LIMIT = 12
PIC_DIAGNOSTIC_CHAR_LIMIT = 240
UNSAFE_SHELL_RE = re.compile(
    r"(?i)\b(rm\s+-rf|del\s+/[fsq]|format\b|curl\b.*\|\s*(sh|bash|pwsh|powershell)|"
    r"wget\b.*\|\s*(sh|bash|pwsh|powershell)|chmod\s+777|sudo\s+|Invoke-Expression|iex\b)"
)


def evaluate_policy(
    record: InputRecord,
    *,
    input_ref: str,
    mode: PolicyMode = "advisory",
    pic_report: Mapping[str, object] | None = None,
    pic_command_failed: bool = False,
    pic_failure_reason: str | None = None,
) -> BridgeDecision:
    reasons: list[str] = []
    missing: list[str] = []
    decision = _base_decision(record, reasons, missing)
    pic_used = pic_report is not None or pic_command_failed
    pic_accepted: bool | None = None
    pic_workflow_usable: bool | None = None
    pic_operationally_usable: bool | None = None
    pic_settled: bool | None = None
    residual_summary: dict[str, float] = {}
    pic_diagnostics = PicDiagnostics()

    if pic_command_failed:
        reasons.append(pic_failure_reason or "PIC command failed in PIC-backed mode")
        decision = "block" if mode == "enforce" else _max_decision(decision, "defer")

    if pic_report is not None:
        pic_accepted = _as_bool(pic_report.get("accepted"))
        pic_workflow_usable = _as_bool(pic_report.get("workflow_usable"))
        pic_operationally_usable = _as_bool(pic_report.get("operationally_usable"))
        pic_settled = _as_bool(pic_report.get("settled"))
        residual_summary = _float_mapping(pic_report.get("residual_summary"))
        pic_diagnostics = _pic_diagnostics_from_report(pic_report)
        missing.extend(_missing_from_pic(pic_report))
        if pic_settled is False:
            reasons.append("PIC settled=false means review is incomplete, not a command failure")
        if pic_accepted is True:
            reasons.append("PIC accepted=true is not permission to execute")
        if pic_workflow_usable is True:
            reasons.append("PIC workflow_usable=true is routing-only review context")
        if pic_workflow_usable is False:
            reasons.append("PIC workflow_usable=false; preserve review data before reuse")
            decision = _max_decision(decision, "defer")
        if pic_operationally_usable is False:
            reasons.append("PIC operationally_usable=false; preserve unresolved work")
            if getattr(record, "risk_level", "low") in {"high", "critical"}:
                decision = _max_decision(decision, "defer")

    decision = _apply_mode(record, mode, decision, reasons, missing)

    return make_decision(
        record,
        input_ref=input_ref,
        mode=mode,
        decision=decision,
        reasons=reasons or ["policy completed with no blocking reason"],
        missing_obligations=missing,
        residual_summary=residual_summary,
        pic_used=pic_used,
        pic_accepted=pic_accepted,
        pic_workflow_usable=pic_workflow_usable,
        pic_operationally_usable=pic_operationally_usable,
        pic_settled=pic_settled,
        pic_diagnostics=pic_diagnostics,
    )


def _apply_mode(
    record: InputRecord,
    mode: PolicyMode,
    decision: DecisionName,
    reasons: list[str],
    missing: list[str],
) -> DecisionName:
    if mode == "observe":
        reasons.append("review observation only")
        if decision == "block" and not _has_hard_hazard(record):
            return "defer"
        return decision
    if mode == "advisory":
        reasons.append("advisory decision does not bypass OpenClaw approvals")
        return decision
    reasons.append("enforce mode applies stronger external-effect policy")
    return _enforce_decision(record, decision, reasons, missing)


def _enforce_decision(
    record: InputRecord,
    decision: DecisionName,
    reasons: list[str],
    missing: list[str],
) -> DecisionName:
    if isinstance(record, OpenClawActionProposal):
        kind = record.action_kind.lower()
        args_text = str(record.tool_arguments)
        if _contains_credential_signal(kind, args_text):
            return "block"
        if kind in DESTRUCTIVE_ACTION_KINDS:
            return "block"
        if kind in SHELL_ACTION_KINDS:
            if not record.tool_arguments or _unknown_shell(record.tool_arguments):
                return "block"
            if UNSAFE_SHELL_RE.search(args_text):
                return "block"
        if record.risk_level == "critical" and not record.requires_human_confirmation:
            return "block"
        if record.external_effect and not record.rollback_plan:
            if "rollback_plan" not in missing:
                missing.append("rollback_plan")
            decision = _max_decision(decision, "defer")
        if record.external_effect and (record.missing_evidence or not record.evidence_refs):
            decision = _max_decision(decision, "defer")
        return decision
    if isinstance(record, OpenClawSkillInstall):
        if record.credential_access_required or record.risk_level == "critical":
            return "block"
        if record.shell_required or record.network_required or record.file_write_required:
            return _max_decision(decision, "defer")
    if isinstance(record, OpenClawMemoryWrite) and record.risk_level == "critical":
        return "block"
    return decision


def _has_hard_hazard(record: InputRecord) -> bool:
    if isinstance(record, OpenClawActionProposal):
        kind = record.action_kind.lower()
        args_text = str(record.tool_arguments)
        return (
            _contains_credential_signal(kind, args_text)
            or kind in DESTRUCTIVE_ACTION_KINDS
            or (
                kind in SHELL_ACTION_KINDS
                and (
                    not record.tool_arguments
                    or _unknown_shell(record.tool_arguments)
                    or bool(UNSAFE_SHELL_RE.search(args_text))
                )
            )
        )
    if isinstance(record, OpenClawSkillInstall):
        return record.credential_access_required or any(
            permission.lower() in UNCLEAR_PERMISSIONS for permission in record.requested_permissions
        )
    return False


def _base_decision(record: InputRecord, reasons: list[str], missing: list[str]) -> DecisionName:
    if isinstance(record, OpenClawActionProposal):
        return _action_decision(record, reasons, missing)
    if isinstance(record, OpenClawResultClaim):
        return _result_decision(record, reasons, missing)
    if isinstance(record, OpenClawMemoryWrite):
        return _memory_decision(record, reasons, missing)
    if isinstance(record, OpenClawSkillInstall):
        return _skill_install_decision(record, reasons, missing)
    reasons.append("unsupported record type")
    return "block"


def _action_decision(
    record: OpenClawActionProposal, reasons: list[str], missing: list[str]
) -> DecisionName:
    decision: DecisionName = "allow"
    kind = record.action_kind.lower()
    args_text = str(record.tool_arguments)
    if _contains_credential_signal(kind, args_text):
        reasons.append("credential or token handling requires blocking review")
        return "block"
    if record.risk_level == "critical":
        reasons.append("critical risk action requires explicit approval and no residual hazard")
        decision = "block" if not record.requires_human_confirmation else "defer"
    elif record.risk_level == "high":
        reasons.append("high risk action defers by default")
        decision = "defer"
    elif record.risk_level == "medium":
        decision = "warn"
    if record.external_effect and not record.rollback_plan:
        reasons.append("external-effect action has no rollback plan")
        missing.append("rollback_plan")
        decision = _max_decision(decision, "defer")
    if record.external_effect and record.missing_evidence:
        reasons.append("external-effect action has missing evidence")
        missing.extend(record.missing_evidence)
        decision = _max_decision(decision, "defer")
    if record.external_effect and not record.evidence_refs:
        reasons.append("external-effect action has no evidence refs")
        missing.append("evidence_refs")
        decision = _max_decision(decision, "defer")
    if kind in DESTRUCTIVE_ACTION_KINDS:
        reasons.append("destructive or irreversible action is blocked unless separately approved")
        decision = "block"
    if kind in SHELL_ACTION_KINDS:
        if not record.tool_arguments or _unknown_shell(record.tool_arguments):
            reasons.append("shell action has unknown command contents")
            return "block"
        if UNSAFE_SHELL_RE.search(args_text):
            reasons.append("unsafe shell command pattern")
            return "block"
    if kind in NETWORK_ACTION_KINDS and record.risk_level in {"high", "critical"}:
        reasons.append("high-risk network action needs review")
        decision = _max_decision(decision, "defer")
    if record.requires_human_confirmation and decision == "allow":
        reasons.append("human confirmation required by proposal")
        decision = "defer"
    if not record.external_effect and record.missing_evidence:
        reasons.append("low risk non-external action carries residual evidence")
        decision = "warn"
        missing.extend(record.missing_evidence)
    return decision


def _result_decision(
    record: OpenClawResultClaim, reasons: list[str], missing: list[str]
) -> DecisionName:
    decision: DecisionName = "warn"
    if not record.evidence_refs:
        reasons.append("result claim has no evidence refs")
        missing.append("evidence_refs")
        decision = "defer"
    if not record.logs_refs:
        reasons.append("result claim has no logs refs")
        missing.append("logs_refs")
        decision = "defer"
    if record.unresolved_items:
        reasons.append("result claim has unresolved items")
        missing.extend(record.unresolved_items)
        decision = "defer"
    if not record.rollback_available:
        reasons.append("result claim has no rollback available")
    return decision


def _memory_decision(
    record: OpenClawMemoryWrite, reasons: list[str], missing: list[str]
) -> DecisionName:
    if record.risk_level == "critical":
        reasons.append("critical memory write risk")
        return "block"
    if record.risk_level == "high":
        reasons.append("high risk memory write defers by default")
        return "defer"
    if record.should_be_persistent and record.claim_type == "fact" and not record.evidence_refs:
        reasons.append("persistent factual memory write lacks evidence")
        missing.append("evidence_refs")
        return "defer"
    if record.should_be_persistent and record.claim_type in {"unknown", "hypothesis"}:
        reasons.append("persistent uncertain memory write needs review")
        return "defer"
    if not record.evidence_refs and record.claim_type == "fact":
        reasons.append("factual memory write carries unsupported evidence residual")
        missing.append("evidence_refs")
        return "warn"
    return "allow"


def _skill_install_decision(
    record: OpenClawSkillInstall, reasons: list[str], missing: list[str]
) -> DecisionName:
    if record.credential_access_required:
        reasons.append("skill install requests credential access")
        return "block"
    if record.risk_level == "critical":
        reasons.append("critical risk skill install")
        return "block"
    decision: DecisionName = "defer" if record.risk_level in {"medium", "high"} else "warn"
    if not record.source_ref:
        reasons.append("skill install source is unclear")
        missing.append("source_ref")
        decision = _max_decision(decision, "defer")
    if not record.requested_permissions:
        reasons.append("skill install permissions are unclear")
        missing.append("requested_permissions")
        decision = _max_decision(decision, "defer")
    if any(
        permission.lower() in UNCLEAR_PERMISSIONS for permission in record.requested_permissions
    ):
        reasons.append("skill install requests unclear broad permissions")
        decision = "block"
    if record.shell_required and not record.install_steps:
        reasons.append("shell-required skill install has no install steps")
        return "block"
    if record.shell_required or record.network_required or record.file_write_required:
        reasons.append("skill install requires shell, network, or file write review")
        decision = _max_decision(decision, "defer")
    return decision


def _contains_credential_signal(kind: str, text: str) -> bool:
    lowered = f"{kind} {text}".lower()
    return any(word in lowered for word in CREDENTIAL_WORDS)


def _unknown_shell(arguments: Mapping[str, object]) -> bool:
    command = arguments.get("command") or arguments.get("cmd") or arguments.get("script")
    return not isinstance(command, str) or not command.strip()


DECISION_ORDER = {"allow": 0, "warn": 1, "defer": 2, "block": 3}


def _max_decision(left: DecisionName, right: DecisionName) -> DecisionName:
    return left if DECISION_ORDER[left] >= DECISION_ORDER[right] else right


def _as_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _float_mapping(value: object) -> dict[str, float]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, float] = {}
    for key, raw in value.items():
        if isinstance(raw, int | float):
            result[str(key)] = float(raw)
    return result


def _missing_from_pic(report: Mapping[str, object]) -> list[str]:
    missing: list[str] = []
    for source in _pic_sources(report):
        for key in ("missing_obligations", "unresolved_obligations", "settled_blockers"):
            raw = source.get(key)
            if isinstance(raw, list):
                missing.extend(str(item) for item in raw)
    return missing


def _pic_diagnostics_from_report(report: Mapping[str, object]) -> PicDiagnostics:
    runtime_report = _runtime_report_from_pic(report)
    return PicDiagnostics(
        workflow_usable=_as_bool(report.get("workflow_usable")),
        unresolved_obligations=_diagnostic_items(
            report,
            runtime_report,
            "unresolved_obligations",
            fallback_key="missing_obligations",
        ),
        next_safe_actions=_diagnostic_items(report, runtime_report, "next_safe_actions"),
        schema_refs=_diagnostic_items(report, runtime_report, "schema_refs"),
        safety_invariants=_diagnostic_items(report, runtime_report, "safety_invariants"),
        checked_outputs=_checked_output_items(report),
        phase_diagnostics=_phase_diagnostic_items(report, runtime_report),
        agent_tasks=_diagnostic_items(report, runtime_report, "agent_tasks"),
        route_execution_requests=_diagnostic_items(
            report, runtime_report, "route_execution_requests"
        ),
        residual_ledger=_diagnostic_items(report, runtime_report, "residual_ledger"),
        provenance_refs=_diagnostic_items(
            report,
            runtime_report,
            "provenance_refs",
            fallback_key="provenance",
        ),
    )


def _runtime_report_from_pic(report: Mapping[str, object]) -> Mapping[str, object]:
    runtime = report.get("runtime_report")
    if isinstance(runtime, Mapping):
        return runtime
    intake = report.get("intake_report")
    if isinstance(intake, Mapping):
        nested_runtime = intake.get("runtime_report")
        if isinstance(nested_runtime, Mapping):
            return nested_runtime
    return {}


def _pic_sources(report: Mapping[str, object]) -> list[Mapping[str, object]]:
    sources: list[Mapping[str, object]] = [report]
    runtime = _runtime_report_from_pic(report)
    if runtime:
        sources.append(runtime)
    intake = report.get("intake_report")
    if isinstance(intake, Mapping):
        sources.append(intake)
    return sources


def _checked_output_items(report: Mapping[str, object]) -> list[str]:
    raw = report.get("checked_outputs")
    if not isinstance(raw, Mapping):
        return []
    return _cap_diagnostic_items([f"{key}: {value}" for key, value in raw.items()])


def _phase_diagnostic_items(
    report: Mapping[str, object], runtime_report: Mapping[str, object]
) -> list[str]:
    raw_items: list[object] = []
    for source in (report, runtime_report):
        for key in (
            "phase_gap_vector",
            "top_bottlenecks",
            "candidate_only_reasons",
            "cannot_promote_because",
            "settled_blockers",
            "phase_control_audit",
            "frontier_debt_report",
            "bottleneck_witness_reports",
        ):
            raw_items.extend(_iter_diagnostic_values(source.get(key)))
    return _cap_diagnostic_items(raw_items)


def _diagnostic_items(
    report: Mapping[str, object],
    runtime_report: Mapping[str, object],
    key: str,
    *,
    fallback_key: str | None = None,
) -> list[str]:
    raw_items: list[object] = []
    for source in (report, runtime_report):
        raw = source.get(key)
        if raw is None and fallback_key is not None:
            raw = source.get(fallback_key)
        raw_items.extend(_iter_diagnostic_values(raw))
    return _cap_diagnostic_items(raw_items)


def _iter_diagnostic_values(raw: object) -> list[object]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, tuple):
        return list(raw)
    return [raw]


def _cap_diagnostic_items(items: list[object]) -> list[str]:
    capped: list[str] = []
    for item in items[:PIC_DIAGNOSTIC_ITEM_LIMIT]:
        text = sanitize_public_text(_diagnostic_to_text(item))
        if len(text) > PIC_DIAGNOSTIC_CHAR_LIMIT:
            text = f"{text[: PIC_DIAGNOSTIC_CHAR_LIMIT - 3]}..."
        capped.append(text)
    return capped


def _diagnostic_to_text(item: object) -> str:
    if isinstance(item, str):
        return item
    try:
        return json.dumps(item, sort_keys=True, ensure_ascii=True)
    except TypeError:
        return str(item)
