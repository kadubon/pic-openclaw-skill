from __future__ import annotations

import re

from pic_openclaw_skill.cli import load_input
from pic_openclaw_skill.formatter import render_feedback
from pic_openclaw_skill.policy import evaluate_policy
from tests.conftest import ROOT


def test_docs_state_security_boundary() -> None:
    text = (ROOT / "docs" / "security-boundary.md").read_text(encoding="utf-8")
    for phrase in [
        "does not execute proposed actions",
        "does not run proposed shell commands",
        "does not clone PIC automatically",
        "does not install PIC automatically",
        "does not prove correctness",
        "does not prove real ASI",
        "does not validate external-world truth",
        "PIC reports are diagnostic artifacts",
        "Users remain responsible for action approval",
    ]:
        assert phrase in text


def test_docs_keep_skill_only_independent_from_pic_python_and_uv() -> None:
    combined = "\n".join(
        [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "setup.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "pic-backed-mode.md").read_text(encoding="utf-8"),
        ]
    )
    assert "does not require PIC, Python, uv" in combined
    assert "Clone PIC only when you want the optional full workflow path" in combined
    assert "PIC clone is optional" not in combined


def test_docs_match_openclaw_install_and_clawhub_boundaries() -> None:
    combined = "\n".join(
        [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "setup.md").read_text(encoding="utf-8"),
        ]
    )
    assert "openclaw skills install git:kadubon/pic-openclaw-skill@main" in combined
    assert "<workspace>/skills/pic-residual-guard" in combined
    assert "~/.openclaw/skills/pic-residual-guard" in combined
    assert "ClawHub publication is out of scope" in combined
    assert "requires a separate license decision" in combined
    assert "clawhub publish" not in combined.lower()


def test_docs_include_openclaw_security_model_boundaries() -> None:
    combined = "\n".join(
        [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "security-boundary.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "threat-model.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "skill-only-mode.md").read_text(encoding="utf-8"),
        ]
    )
    for phrase in [
        "not a replacement for OpenClaw sandboxing",
        "openclaw security audit",
        "exec on deny or ask",
        "workspace-only",
        "skill allowlists",
        "single-operator trust boundary",
        "hostile multi-tenant security boundary",
    ]:
        assert phrase in combined


def test_docs_describe_pic_diagnostics_as_non_executable() -> None:
    combined = "\n".join(
        [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "pic-backed-mode.md").read_text(encoding="utf-8"),
        ]
    )
    for phrase in [
        "agent_tasks",
        "route_execution_requests",
        "residual_ledger",
        "provenance",
        "diagnostic only",
        "not execution instructions",
    ]:
        assert phrase in combined


def test_feedback_has_no_secret_or_local_path_leaks() -> None:
    path = ROOT / "examples" / "bridge" / "openclaw_action_shell.json"
    record = load_input(path)
    decision = evaluate_policy(record, input_ref=str(path))
    feedback = render_feedback(decision, record)
    assert str(ROOT) not in feedback
    assert not re.search(r"[A-Za-z]:\\", feedback)
    assert ("PRIVATE" + " KEY") not in feedback
    assert ("api_" + "key=") not in feedback.lower()


def test_examples_do_not_execute_shell_commands() -> None:
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_shell.json")
    assert record.tool_arguments == {}
    decision = evaluate_policy(record, input_ref="openclaw_action_shell.json")
    assert decision.decision == "block"
