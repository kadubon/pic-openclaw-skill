from __future__ import annotations

import json

from typer.testing import CliRunner

from pic_openclaw_skill.cli import app
from pic_openclaw_skill.pic_backend import PicBackendError
from tests.conftest import ROOT

runner = CliRunner()


def test_no_pic_cli_works_on_examples(tmp_path) -> None:  # type: ignore[no-untyped-def]
    for path in sorted((ROOT / "examples" / "bridge").glob("openclaw_*.json")):
        output = tmp_path / f"{path.stem}.decision.json"
        feedback = tmp_path / f"{path.stem}.md"
        result = runner.invoke(
            app,
            [
                "--input",
                str(path),
                "--no-pic",
                "--output",
                str(output),
                "--feedback",
                str(feedback),
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["mode"] == "advisory"
        assert data["policy_allows_next_step"] is (data["decision"] in {"allow", "warn"})
        assert data["allowed_to_execute"] is (data["decision"] == "allow")
        assert data["pic_diagnostics"]["workflow_usable"] is None
        assert data["pic_diagnostics"]["agent_tasks"] == []
        assert data["pic_diagnostics"]["next_safe_actions"] == []
        assert data["pic_diagnostics"]["phase_diagnostics"] == []
        assert "Generated agent output is a candidate, not verified work." in feedback.read_text(
            encoding="utf-8"
        )


def test_default_cli_is_skill_only_on_examples(tmp_path) -> None:  # type: ignore[no-untyped-def]
    for path in sorted((ROOT / "examples" / "bridge").glob("openclaw_*.json")):
        output = tmp_path / f"{path.stem}.default.decision.json"
        result = runner.invoke(
            app,
            [
                "--input",
                str(path),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["pic_used"] is False
        assert data["mode"] == "advisory"
        assert data["pic_diagnostics"]["workflow_usable"] is None
        assert data["pic_diagnostics"]["agent_tasks"] == []
        assert data["allowed_to_execute"] is (data["decision"] == "allow")


def test_no_pic_rejects_pic_options() -> None:
    result = runner.invoke(
        app,
        [
            "--input",
            str(ROOT / "examples" / "bridge" / "openclaw_action_email.json"),
            "--no-pic",
            "--pic-command",
            "pic",
        ],
    )
    assert result.exit_code != 0
    assert "PIC clone is optional" in result.output


def test_cli_creates_output_parent_directories(tmp_path) -> None:  # type: ignore[no-untyped-def]
    output = tmp_path / "nested" / "decisions" / "decision.json"
    feedback = tmp_path / "nested" / "feedback" / "feedback.md"
    result = runner.invoke(
        app,
        [
            "--input",
            str(ROOT / "examples" / "bridge" / "openclaw_action_email.json"),
            "--output",
            str(output),
            "--feedback",
            str(feedback),
        ],
    )
    assert result.exit_code == 0, result.output
    assert output.exists()
    assert feedback.exists()


def test_cli_pic_timeout_becomes_sanitized_diagnostic(monkeypatch, tmp_path) -> None:  # type: ignore[no-untyped-def]
    def fake_backend(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise PicBackendError(
            "PIC command timed out",
            stderr_tail="D:" + "\\Private\\workspace " + ("api_" + "key=redacted-value"),
            timeout=True,
        )

    monkeypatch.setattr("pic_openclaw_skill.cli.run_pic_backend", fake_backend)
    output = tmp_path / "decision.json"
    result = runner.invoke(
        app,
        [
            "--input",
            str(ROOT / "examples" / "bridge" / "openclaw_action_file_write.json"),
            "--pic-command",
            "pic",
            "--pic-timeout-seconds",
            "0.01",
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads(output.read_text(encoding="utf-8"))
    reasons = "\n".join(data["reasons"])
    assert data["pic_used"] is True
    assert data["decision"] == "defer"
    assert "PIC command timed out" in reasons
    assert "timeout=true" in reasons
    assert "D:" not in reasons
    assert ("api_" + "key=") not in reasons
