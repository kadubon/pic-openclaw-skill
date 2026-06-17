from __future__ import annotations

import json

from pic_openclaw_skill.cli import load_input
from pic_openclaw_skill.formatter import render_feedback
from pic_openclaw_skill.policy import evaluate_policy
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
    assert any("curl" in item for item in decision.pic_diagnostics.route_execution_requests)
    assert all("curl" not in step for step in decision.safe_next_steps)
    assert "Diagnostic only; do not execute" in feedback
    assert "D:" not in serialized
    assert "D:" not in feedback
    assert ("api_" + "key=") not in serialized
    assert ("api_" + "key=") not in feedback
