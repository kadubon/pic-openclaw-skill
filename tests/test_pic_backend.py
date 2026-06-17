from __future__ import annotations

import json
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
    assert calls[0]["command"][:5] == ["uv", "run", "pic", "agent", "intake"]
