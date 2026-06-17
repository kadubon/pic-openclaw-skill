from __future__ import annotations

# ruff: noqa: I001

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pic_openclaw_skill.formatter import render_feedback
from pic_openclaw_skill.records import BridgeDecision

app = typer.Typer(add_completion=False)


@app.command()
def main(
    decision: Annotated[Path, typer.Option("--decision")],
    output: Annotated[Path | None, typer.Option("--output")] = None,
) -> None:
    payload = json.loads(decision.read_text(encoding="utf-8"))
    rendered = render_feedback(BridgeDecision.model_validate(payload))
    if output is None:
        typer.echo(rendered)
    else:
        output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    app()
