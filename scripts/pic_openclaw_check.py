from __future__ import annotations

# ruff: noqa: I001

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pic_openclaw_skill.cli import app


if __name__ == "__main__":
    app()
