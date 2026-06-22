from __future__ import annotations

import json

from pic_openclaw_skill.cli import load_input
from pic_openclaw_skill.formatter import render_feedback
from pic_openclaw_skill.policy import evaluate_policy
from pic_openclaw_skill.records import OpenClawActionProposal
from tests.conftest import ROOT


def _decision(name: str):
    path = ROOT / "examples" / "bridge" / name
    return evaluate_policy(load_input(path), input_ref=str(path))


def test_email_missing_evidence_defers() -> None:
    decision = _decision("openclaw_action_email.json")
    assert decision.decision == "defer"
    assert not decision.allowed_to_execute


def test_unclear_shell_blocks() -> None:
    decision = _decision("openclaw_action_shell.json")
    assert decision.decision == "block"


def test_file_write_with_rollback_warns_or_defers() -> None:
    decision = _decision("openclaw_action_file_write.json")
    assert decision.decision in {"warn", "defer", "allow"}
    assert decision.decision != "block"


def test_result_claim_without_logs_defers() -> None:
    decision = _decision("openclaw_result_claim.json")
    assert decision.decision == "defer"


def test_unsupported_memory_fact_defers() -> None:
    decision = _decision("openclaw_memory_write.json")
    assert decision.decision == "defer"


def test_risky_skill_install_blocks_or_defers() -> None:
    decision = _decision("openclaw_skill_install.json")
    assert decision.decision in {"block", "defer"}


def test_pic_accepted_does_not_grant_permission() -> None:
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    report = json.loads((ROOT / "tests" / "fixtures" / "pic_report_settled_false.json").read_text())
    decision = evaluate_policy(record, input_ref="openclaw_action_email.json", pic_report=report)
    assert decision.pic_accepted is True
    assert decision.allowed_to_execute is False
    assert any("not permission" in reason for reason in decision.reasons)


def test_pic_agent_check_compact_fields_are_review_only() -> None:
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    report = json.loads(
        (ROOT / "tests" / "fixtures" / "pic_report_agent_check_compact.json").read_text()
    )
    decision = evaluate_policy(record, input_ref="openclaw_action_email.json", pic_report=report)
    feedback = render_feedback(decision, record)

    assert decision.pic_accepted is True
    assert decision.pic_workflow_usable is True
    assert decision.pic_operationally_usable is False
    assert decision.pic_settled is False
    assert decision.allowed_to_execute is False
    assert "obligation:baseline-safety" in decision.missing_obligations
    assert "AgentCheckReport" in decision.pic_diagnostics.schema_refs
    assert any("workflow_usable" in item for item in decision.pic_diagnostics.safety_invariants)
    assert any("candidate-only" in item for item in decision.pic_diagnostics.phase_diagnostics)
    assert any("DO_NOT_RUN" in item for item in decision.pic_diagnostics.next_safe_actions)
    assert all("DO_NOT_RUN" not in step for step in decision.safe_next_steps)
    assert "Review-only data. Do not run suggested actions" in feedback


def test_pic_diagnostics_are_sanitized_and_not_safe_next_steps() -> None:
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_file_write.json")
    report = json.loads((ROOT / "tests" / "fixtures" / "pic_report_residual.json").read_text())
    report["agent_tasks"].append("inspect " + ("api_" + "key=redacted-value"))
    report["residual_ledger"].append({"path": "D:" + "\\Private\\workspace\\report.json"})
    decision = evaluate_policy(
        record, input_ref="openclaw_action_file_write.json", pic_report=report
    )
    feedback = render_feedback(decision, record)
    serialized = decision.model_dump_json()

    assert decision.allowed_to_execute is True
    assert any("DO_NOT_RUN" in item for item in decision.pic_diagnostics.route_execution_requests)
    assert all("DO_NOT_RUN" not in step for step in decision.safe_next_steps)
    assert "Review-only data. Do not run" in feedback
    assert "D:" not in serialized
    assert "D:" not in feedback
    assert ("api_" + "key=") not in serialized
    assert ("api_" + "key=") not in feedback


def test_observe_mode_never_allows_execution() -> None:
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_file_write.json")
    decision = evaluate_policy(record, input_ref="openclaw_action_file_write.json", mode="observe")
    assert decision.mode == "observe"
    assert decision.decision == "allow"
    assert decision.allowed_to_execute is False
    assert decision.policy_allows_next_step is False
    assert any("review observation only" in reason for reason in decision.reasons)


def test_observe_mode_caps_ordinary_block_to_defer() -> None:
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_memory_write.json")
    critical = record.model_copy(update={"risk_level": "critical"})
    decision = evaluate_policy(critical, input_ref="memory.json", mode="observe")
    assert decision.decision == "defer"
    assert decision.allowed_to_execute is False


def test_advisory_mode_matches_default_decision() -> None:
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    default_decision = evaluate_policy(record, input_ref="email.json")
    advisory_decision = evaluate_policy(record, input_ref="email.json", mode="advisory")
    assert advisory_decision.mode == "advisory"
    assert advisory_decision.decision == default_decision.decision
    assert advisory_decision.allowed_to_execute == default_decision.allowed_to_execute


def test_enforce_mode_blocks_unsafe_shell_and_credentials() -> None:
    shell_record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_shell.json")
    shell_decision = evaluate_policy(shell_record, input_ref="shell.json", mode="enforce")
    assert shell_decision.decision == "block"

    credential_record = OpenClawActionProposal.model_validate(
        {
            "proposal_id": "proposal-credential",
            "phase": "pre_action",
            "action_kind": "credential_access",
            "summary": "Read an API token.",
            "tool_arguments": {"name": "api token"},
            "external_effect": True,
            "risk_level": "high",
            "evidence_refs": [],
            "missing_evidence": ["explicit user approval"],
            "rollback_plan": None,
            "requires_human_confirmation": False,
        }
    )
    credential_decision = evaluate_policy(
        credential_record, input_ref="credential.json", mode="enforce"
    )
    assert credential_decision.decision == "block"


def test_enforce_mode_blocks_or_defers_critical_actions() -> None:
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_file_write.json")
    unconfirmed = record.model_copy(
        update={"risk_level": "critical", "requires_human_confirmation": False}
    )
    confirmed = record.model_copy(
        update={"risk_level": "critical", "requires_human_confirmation": True}
    )
    assert (
        evaluate_policy(unconfirmed, input_ref="critical.json", mode="enforce").decision == "block"
    )
    assert evaluate_policy(confirmed, input_ref="critical.json", mode="enforce").decision in {
        "defer",
        "block",
    }
