from __future__ import annotations

from pic_openclaw_skill.cli import load_input
from pic_openclaw_skill.formatter import render_feedback
from pic_openclaw_skill.policy import evaluate_policy
from tests.conftest import ROOT


def test_feedback_renderer_includes_required_safety_phrases() -> None:
    path = ROOT / "examples" / "bridge" / "openclaw_action_email.json"
    record = load_input(path)
    decision = evaluate_policy(record, input_ref=str(path))
    feedback = render_feedback(decision, record)
    required = [
        "Generated agent output is a candidate, not verified work.",
        "`settled=false` is diagnostic, not a command failure.",
        "does not prove correctness, real ASI, external-world truth, or action safety",
        "It does not execute the proposed action.",
    ]
    for phrase in required:
        assert phrase in feedback


def test_feedback_does_not_include_local_absolute_path() -> None:
    path = ROOT / "examples" / "bridge" / "openclaw_action_email.json"
    record = load_input(path)
    decision = evaluate_policy(record, input_ref=str(path))
    feedback = render_feedback(decision, record)
    assert str(ROOT) not in feedback
    assert "C:\\" not in feedback
