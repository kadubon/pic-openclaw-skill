from __future__ import annotations

import json

from typer.testing import CliRunner

from pic_openclaw_skill.cli import app
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
        assert data["allowed_to_execute"] is (data["decision"] == "allow")
        assert data["pic_diagnostics"] == {
            "agent_tasks": [],
            "route_execution_requests": [],
            "residual_ledger": [],
            "provenance_refs": [],
        }
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
