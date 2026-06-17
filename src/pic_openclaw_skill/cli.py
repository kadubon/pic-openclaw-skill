"""Typer CLI for PIC OpenClaw checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Literal

import typer

from pic_openclaw_skill.formatter import render_feedback
from pic_openclaw_skill.pic_backend import PicBackendError, run_pic_backend
from pic_openclaw_skill.policy import evaluate_policy
from pic_openclaw_skill.records import (
    BridgeDecision,
    InputRecord,
    OpenClawActionProposal,
    OpenClawMemoryWrite,
    OpenClawResultClaim,
    OpenClawSkillInstall,
)

app = typer.Typer(add_completion=False, help="PIC OpenClaw action proposal checker.")


def main(
    input_path: Annotated[Path, typer.Option("--input", help="OpenClaw proposal JSON input.")],
    mode: Annotated[
        Literal["observe", "advisory", "enforce"],
        typer.Option("--mode", help="Bridge mode; policy remains deterministic."),
    ] = "advisory",
    pic_repo: Annotated[Path | None, typer.Option("--pic-repo", help="Local PIC checkout.")] = None,
    pic_command: Annotated[
        str | None,
        typer.Option(
            "--pic-command",
            help="Existing PIC command to run, for example 'pic' or 'uv run pic'.",
        ),
    ] = None,
    profile: Annotated[str, typer.Option("--profile", help="PIC runtime profile.")] = "development",
    output: Annotated[Path | None, typer.Option("--output", help="Decision JSON output.")] = None,
    feedback: Annotated[
        Path | None, typer.Option("--feedback", help="Feedback markdown output.")
    ] = None,
    pic_report: Annotated[
        Path | None, typer.Option("--pic-report", help="PIC JSON report path.")
    ] = None,
    no_pic: Annotated[bool, typer.Option("--no-pic", help="Run skill-only policy.")] = False,
) -> None:
    del mode
    record = load_input(input_path)
    if no_pic and (pic_repo is not None or pic_command is not None):
        _configuration_error(
            "Use --no-pic without --pic-repo or --pic-command. PIC clone is optional."
        )

    pic_payload: dict[str, object] | None = None
    pic_failed = False
    should_use_pic = not no_pic and (pic_command is not None or pic_repo is not None)
    if should_use_pic:
        effective_pic_command = pic_command or "uv run pic"
        try:
            pic_payload = run_pic_backend(
                record,
                pic_repo=pic_repo,
                pic_command=effective_pic_command,
                profile=profile,
                pic_report_path=pic_report,
            )
        except PicBackendError:
            pic_failed = True

    decision = evaluate_policy(
        record,
        input_ref=str(input_path),
        pic_report=pic_payload,
        pic_command_failed=pic_failed,
    )
    write_outputs(decision, record, output, feedback)


app.command()(main)


def load_input(path: Path) -> InputRecord:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise typer.BadParameter("input JSON must contain an object")
    phase = data.get("phase")
    if phase == "pre_action":
        return OpenClawActionProposal.model_validate(data)
    if phase == "post_action":
        return OpenClawResultClaim.model_validate(data)
    if phase == "memory_write":
        return OpenClawMemoryWrite.model_validate(data)
    if phase == "skill_install":
        return OpenClawSkillInstall.model_validate(data)
    raise typer.BadParameter(
        "input phase must be pre_action, post_action, memory_write, or skill_install"
    )


def _configuration_error(message: str) -> None:
    typer.echo(message, err=True)
    raise typer.Exit(2)


def write_outputs(
    decision: BridgeDecision,
    record: InputRecord,
    output: Path | None,
    feedback: Path | None,
) -> None:
    payload = json.dumps(decision.model_dump(mode="json"), indent=2, sort_keys=True)
    if output is None:
        typer.echo(payload)
    else:
        output.write_text(payload + "\n", encoding="utf-8")
    if feedback is not None:
        feedback.write_text(render_feedback(decision, record), encoding="utf-8")


if __name__ == "__main__":
    app()
