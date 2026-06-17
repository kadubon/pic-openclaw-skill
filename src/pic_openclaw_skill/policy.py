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
    pic_report: Mapping[str, object] | None = None,
    pic_command_failed: bool = False,
) -> BridgeDecision:
    reasons: list[str] = []
    missing: list[str] = []
    decision = _base_decision(record, reasons, missing)
    pic_used = pic_report is not None or pic_command_failed
    pic_accepted: bool | None = None
    pic_operationally_usable: bool | None = None
    pic_settled: bool | None = None
    residual_summary: dict[str, float] = {}
    pic_diagnostics = PicDiagnostics()

    if pic_command_failed:
        reasons.append("PIC command failed in PIC-backed mode")
        decision = "block"

    if pic_report is not None:
        pic_accepted = _as_bool(pic_report.get("accepted"))
        pic_operationally_usable = _as_bool(pic_report.get("operationally_usable"))
        pic_settled = _as_bool(pic_report.get("settled"))
        residual_summary = _float_mapping(pic_report.get("residual_summary"))
        pic_diagnostics = _pic_diagnostics_from_report(pic_report)
        missing.extend(_missing_from_pic(pic_report))
        if pic_settled is False:
            reasons.append("PIC settled=false is diagnostic, not a command failure")
        if pic_accepted is True:
            reasons.append("PIC accepted=true is not permission to execute")
        if pic_operationally_usable is False:
            reasons.append("PIC operationally_usable=false; preserve residuals")
            if getattr(record, "risk_level", "low") in {"high", "critical"}:
                decision = _max_decision(decision, "defer")

    return make_decision(
        record,
        input_ref=input_ref,
        decision=decision,
        reasons=reasons or ["policy completed with no blocking reason"],
        missing_obligations=missing,
        residual_summary=residual_summary,
        pic_used=pic_used,
        pic_accepted=pic_accepted,
        pic_operationally_usable=pic_operationally_usable,
        pic_settled=pic_settled,
        pic_diagnostics=pic_diagnostics,
    )


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
    runtime = report.get("runtime_report")
    if isinstance(runtime, Mapping):
        raw = runtime.get("missing_obligations")
        if isinstance(raw, list):
            missing.extend(str(item) for item in raw)
    raw_top = report.get("missing_obligations")
    if isinstance(raw_top, list):
        missing.extend(str(item) for item in raw_top)
    return missing


def _pic_diagnostics_from_report(report: Mapping[str, object]) -> PicDiagnostics:
    runtime = report.get("runtime_report")
    runtime_report = runtime if isinstance(runtime, Mapping) else {}
    return PicDiagnostics(
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
