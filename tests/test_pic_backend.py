from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from pic_openclaw_skill.cli import load_input
from pic_openclaw_skill.pic_backend import PicBackendError, run_pic_backend
from tests.conftest import ROOT


def test_pic_backend_fails_clearly_for_missing_repo(tmp_path: Path) -> None:
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    with pytest.raises(PicBackendError, match="--pic-repo"):
        run_pic_backend(
            record,
            pic_repo=tmp_path / "missing",
            pic_command="uv run pic",
            profile="development",
        )


def test_pic_backend_can_use_existing_pic_command_without_clone(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        calls.append({"command": command, **kwargs})
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "accepted": True,
                    "workflow_usable": True,
                    "operationally_usable": False,
                    "settled": False,
                    "unresolved_obligations": ["mock-obligation"],
                    "residual_summary": {"residual": 1.0},
                    "next_safe_actions": ["inspect only; do not execute"],
                    "schema_refs": ["AgentCheckReport"],
                }
            ),
            encoding="utf-8",
        )

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr("pic_openclaw_skill.pic_backend.subprocess.run", fake_run)
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    report = run_pic_backend(
        record,
        pic_repo=None,
        pic_command="pic",
        profile="development",
    )
    assert report["accepted"] is True
    assert calls[0]["cwd"] is None
    assert calls[0]["command"][:4] == ["pic", "agent", "check", "--compact"]
    assert "--no-allow-live-connectors" in calls[0]["command"]


def test_pic_backend_can_use_legacy_agent_intake_entrypoint(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        calls.append({"command": command, **kwargs})
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "accepted": True,
                    "operationally_usable": False,
                    "settled": False,
                    "residual_summary": {"residual": 1.0},
                    "runtime_report": {"missing_obligations": ["mock-obligation"]},
                }
            ),
            encoding="utf-8",
        )

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr("pic_openclaw_skill.pic_backend.subprocess.run", fake_run)
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    report = run_pic_backend(
        record,
        pic_repo=None,
        pic_command="pic",
        profile="development",
        entrypoint="agent-intake",
    )
    assert report["accepted"] is True
    assert calls[0]["cwd"] is None
    assert calls[0]["command"][:3] == ["pic", "agent", "intake"]


def test_pic_backend_uses_pic_repo_as_cwd_when_configured(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    calls: list[dict[str, object]] = []

    def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        calls.append({"command": command, **kwargs})
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "accepted": True,
                    "workflow_usable": True,
                    "operationally_usable": True,
                    "settled": False,
                    "residual_summary": {},
                    "runtime_report": {"missing_obligations": []},
                }
            ),
            encoding="utf-8",
        )

        class Completed:
            returncode = 0

        return Completed()

    monkeypatch.setattr("pic_openclaw_skill.pic_backend.subprocess.run", fake_run)
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    run_pic_backend(
        record,
        pic_repo=tmp_path,
        pic_command="uv run pic",
        profile="development",
    )
    assert calls[0]["cwd"] == tmp_path.resolve()
    assert calls[0]["command"][:6] == ["uv", "run", "pic", "agent", "check", "--compact"]


def test_pic_backend_creates_pic_report_parent(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text(
            json.dumps(
                {
                    "accepted": True,
                    "operationally_usable": True,
                    "settled": True,
                    "residual_summary": {},
                    "runtime_report": {"missing_obligations": []},
                }
            ),
            encoding="utf-8",
        )

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        return Completed()

    monkeypatch.setattr("pic_openclaw_skill.pic_backend.subprocess.run", fake_run)
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    report_path = tmp_path / "nested" / "pic" / "report.json"
    run_pic_backend(
        record,
        pic_repo=None,
        pic_command="pic",
        profile="development",
        pic_report_path=report_path,
    )
    assert report_path.exists()


def test_pic_backend_nonzero_return_has_sanitized_diagnostics(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        class Completed:
            returncode = 2
            stdout = "partial stdout"
            stderr = "D:" + "\\Private\\workspace " + ("api_" + "key=redacted-value")

        return Completed()

    monkeypatch.setattr("pic_openclaw_skill.pic_backend.subprocess.run", fake_run)
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    with pytest.raises(PicBackendError) as excinfo:
        run_pic_backend(record, pic_repo=None, pic_command="pic", profile="development")
    reason = excinfo.value.public_reason()
    assert "returncode=2" in reason
    assert "D:" not in reason
    assert ("api_" + "key=") not in reason


def test_pic_backend_timeout_has_sanitized_diagnostics(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=kwargs["timeout"],
            output="D:" + "\\Private\\workspace",
            stderr=("api_" + "key=redacted-value"),
        )

    monkeypatch.setattr("pic_openclaw_skill.pic_backend.subprocess.run", fake_run)
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    with pytest.raises(PicBackendError) as excinfo:
        run_pic_backend(
            record,
            pic_repo=None,
            pic_command="pic",
            profile="development",
            timeout_seconds=0.01,
        )
    reason = excinfo.value.public_reason()
    assert "PIC command timed out" in reason
    assert "timeout=true" in reason
    assert "D:" not in reason
    assert ("api_" + "key=") not in reason


def test_pic_backend_invalid_json_reports_safely(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        output_path = Path(command[command.index("--output") + 1])
        output_path.write_text("{not-json", encoding="utf-8")

        class Completed:
            returncode = 0
            stdout = ""
            stderr = ""

        return Completed()

    monkeypatch.setattr("pic_openclaw_skill.pic_backend.subprocess.run", fake_run)
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    with pytest.raises(PicBackendError, match="valid JSON"):
        run_pic_backend(
            record,
            pic_repo=None,
            pic_command="pic",
            profile="development",
            pic_report_path=tmp_path / "report.json",
        )


def test_pic_backend_command_not_found_reports_safely(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    def fake_run(command, **kwargs):  # type: ignore[no-untyped-def]
        raise FileNotFoundError("D:" + "\\Private\\workspace\\pic.exe")

    monkeypatch.setattr("pic_openclaw_skill.pic_backend.subprocess.run", fake_run)
    record = load_input(ROOT / "examples" / "bridge" / "openclaw_action_email.json")
    with pytest.raises(PicBackendError) as excinfo:
        run_pic_backend(record, pic_repo=None, pic_command="missing-pic", profile="development")
    reason = excinfo.value.public_reason()
    assert "could not be started" in reason
    assert "D:" not in reason
