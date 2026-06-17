from __future__ import annotations

from tests.conftest import ROOT


def test_release_files_exist_and_name_v010() -> None:
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## v0.1.0" in changelog
    assert (ROOT / "RELEASE_v0.1.0.md").exists()
    assert (ROOT / "docs" / "release-checklist-v0.1.0.md").exists()
    assert (ROOT / "docs" / "clawhub-readiness.md").exists()


def test_readme_release_wording_is_conservative() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Current release: v0.1.0" in readme
    assert "Recommended first path" in readme
    assert "not yet an official ClawHub submission package" in readme
    assert "official OpenClaw endorsement" not in readme
    assert "official ClawHub publication" not in readme


def test_release_versions_remain_v010() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    root_skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    nested_skill = (ROOT / "skill" / "pic-residual-guard" / "SKILL.md").read_text(encoding="utf-8")
    assert 'version = "0.1.0"' in pyproject
    assert "version: 0.1.0" in root_skill
    assert "version: 0.1.0" in nested_skill
    assert root_skill == nested_skill
