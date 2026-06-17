from __future__ import annotations

import json

from pic_openclaw_skill.cli import load_input
from pic_openclaw_skill.records import (
    OpenClawActionProposal,
    OpenClawMemoryWrite,
    OpenClawResultClaim,
    OpenClawSkillInstall,
)
from tests.conftest import ROOT


def test_example_json_files_validate_against_pydantic_models() -> None:
    expected = {
        "openclaw_action_email.json": OpenClawActionProposal,
        "openclaw_action_shell.json": OpenClawActionProposal,
        "openclaw_action_file_write.json": OpenClawActionProposal,
        "openclaw_result_claim.json": OpenClawResultClaim,
        "openclaw_memory_write.json": OpenClawMemoryWrite,
        "openclaw_skill_install.json": OpenClawSkillInstall,
    }
    for name, model in expected.items():
        path = ROOT / "examples" / "bridge" / name
        data = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(model.model_validate(data), model)
        assert isinstance(load_input(path), model)
