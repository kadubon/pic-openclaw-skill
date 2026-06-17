# Setup

Generated agent output is a candidate, not verified work.

## Skill-only mode

Skill-only mode is the normal OpenClaw path. It does not require PIC, Python, uv, network access, or cloning the PIC repository.

When Git skill installs are allowed, install this public repository directly:

```bash
openclaw skills install git:kadubon/pic-openclaw-skill@main
```

When Git installs are restricted, copy `skill/pic-residual-guard` into the workspace skill root first:

```bash
mkdir -p <workspace>/skills/pic-residual-guard
cp -R skill/pic-residual-guard/* <workspace>/skills/pic-residual-guard/
```

Use `~/.openclaw/skills/pic-residual-guard` only for a shared managed skill visible across local agents. OpenClaw discovers `SKILL.md` under configured skill roots. The root `SKILL.md` is provided for Git/local direct install compatibility; `skill/pic-residual-guard/SKILL.md` is provided for copy-based installs.

ClawHub publication is out of scope for this Apache-2.0 repository. OpenClaw documents ClawHub-published skills as MIT-0, so publishing this skill to ClawHub requires a separate license decision.

## Optional PIC-backed mode

PIC integration is optional and user-configured. If an existing `pic` command is already available, no PIC clone is needed.

Clone PIC only when you want the optional full workflow path with source fixtures and reproducibility:

```bash
git clone https://github.com/kadubon/percolation-inversion-compiler.git
cd percolation-inversion-compiler
uv sync --all-extras --dev
```

This repository does not clone PIC automatically and does not install PIC automatically.
