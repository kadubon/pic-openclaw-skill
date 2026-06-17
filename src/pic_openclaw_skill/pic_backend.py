"""Optional local PIC backend."""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from pic_openclaw_skill.formatter import render_candidate_text
from pic_openclaw_skill.records import InputRecord


class PicBackendError(RuntimeError):
    """Raised when the optional PIC backend cannot produce a report."""


def run_pic_backend(
    record: InputRecord,
    *,
    pic_repo: Path | None,
    pic_command: str,
    profile: str,
    pic_report_path: Path | None = None,
) -> dict[str, object]:
    """Run local PIC agent intake against rendered candidate text."""

    cwd: Path | None = None
    if pic_repo is not None:
        cwd = pic_repo.resolve()
        if not cwd.exists() or not cwd.is_dir():
            raise PicBackendError("--pic-repo must point to an existing local PIC source checkout")
    command_parts = shlex.split(pic_command)
    if not command_parts:
        raise PicBackendError("--pic-command must not be empty")
    with TemporaryDirectory(prefix="pic-openclaw-") as tmp:
        tmp_dir = Path(tmp).resolve()
        candidate_text = tmp_dir / "candidate.txt"
        if pic_report_path is None:
            report_path = tmp_dir / "pic-report.json"
        else:
            report_path = pic_report_path.resolve()
        candidate_text.write_text(render_candidate_text(record), encoding="utf-8")
        command = [
            *command_parts,
            "agent",
            "intake",
            "--text-file",
            str(candidate_text),
            "--profile",
            profile,
            "--output",
            str(report_path),
        ]
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            raise PicBackendError("PIC command failed in PIC-backed mode")
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PicBackendError("PIC report was not valid JSON") from exc
    if not isinstance(payload, dict):
        raise PicBackendError("PIC report must be a JSON object")
    return payload
