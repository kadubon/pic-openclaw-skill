"""Optional local PIC backend."""

from __future__ import annotations

import json
import shlex
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from pic_openclaw_skill.formatter import render_candidate_text
from pic_openclaw_skill.records import InputRecord
from pic_openclaw_skill.safety import sanitize_public_text

PIC_BACKEND_TAIL_LIMIT = 1000


class PicBackendError(RuntimeError):
    """Raised when the optional PIC backend cannot produce a report."""

    def __init__(
        self,
        message: str,
        *,
        returncode: int | None = None,
        stdout_tail: str = "",
        stderr_tail: str = "",
        timeout: bool = False,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.returncode = returncode
        self.stdout_tail = _safe_tail(stdout_tail)
        self.stderr_tail = _safe_tail(stderr_tail)
        self.timeout = timeout

    def public_reason(self) -> str:
        parts = [sanitize_public_text(self.message)]
        if self.returncode is not None:
            parts.append(f"returncode={self.returncode}")
        if self.timeout:
            parts.append("timeout=true")
        if self.stderr_tail:
            parts.append(f"stderr_tail={self.stderr_tail}")
        if self.stdout_tail:
            parts.append(f"stdout_tail={self.stdout_tail}")
        return "; ".join(parts)


def run_pic_backend(
    record: InputRecord,
    *,
    pic_repo: Path | None,
    pic_command: str,
    profile: str,
    pic_report_path: Path | None = None,
    timeout_seconds: float = 120,
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
            report_path.parent.mkdir(parents=True, exist_ok=True)
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
        try:
            completed = subprocess.run(
                command,
                cwd=cwd,
                check=False,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            raise PicBackendError(
                "PIC command timed out",
                stdout_tail=_decode_timeout_output(exc.stdout),
                stderr_tail=_decode_timeout_output(exc.stderr),
                timeout=True,
            ) from exc
        except OSError as exc:
            raise PicBackendError("PIC command could not be started", stderr_tail=str(exc)) from exc
        if completed.returncode != 0:
            raise PicBackendError(
                "PIC command failed in PIC-backed mode",
                returncode=completed.returncode,
                stdout_tail=completed.stdout,
                stderr_tail=completed.stderr,
            )
        try:
            payload = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PicBackendError("PIC report was not valid JSON", stderr_tail=str(exc)) from exc
    if not isinstance(payload, dict):
        raise PicBackendError("PIC report must be a JSON object")
    return payload


def _safe_tail(text: str) -> str:
    return sanitize_public_text(text)[-PIC_BACKEND_TAIL_LIMIT:]


def _decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
