# Release v0.1.0

PIC OpenClaw Skill is a residual-aware action checking skill for OpenClaw agents.

Generated agent output is a candidate, not verified work.

This first release is for users who want a simple manual safety layer before an OpenClaw agent performs external-effect work such as sending email, running shell commands, writing files, making network requests, storing memory, installing skills, or claiming a task is complete.

## What this release provides

- A compact OpenClaw `PIC Residual Guard` skill.
- Skill-only mode that works without PIC, Python, uv, network access, or a PIC clone.
- A helper CLI that can turn action proposals into deterministic JSON decisions and Markdown feedback.
- Optional PIC-backed diagnostics for users who already have a trusted local `pic` command or PIC source checkout.
- Conservative `allow`, `warn`, `defer`, and `block` decisions with `observe`, `advisory`, and `enforce` modes.
- Sanitized feedback that avoids local absolute paths and obvious secret patterns.
- Docs for setup, security boundaries, threat model, licensing, and publication readiness.

## Recommended first use: skill-only mode

Start with manual install. Copy the skill directory into your OpenClaw workspace skill root:

```bash
mkdir -p <workspace>/skills/pic-residual-guard
cp -R skill/pic-residual-guard/* <workspace>/skills/pic-residual-guard/
```

Then review `SKILL.md` and ask OpenClaw to use the PIC Residual Guard before external-effect actions. Skill-only mode is the lowest-friction path and does not require PIC or the helper CLI.

## Optional PIC-backed mode

PIC-backed mode is optional. Use it only when you have reviewed the skill and have a trusted local PIC command, such as:

```bash
uv run pic-openclaw-check \
  --input examples/bridge/openclaw_action_email.json \
  --pic-command "pic" \
  --output bridge-decision.json \
  --feedback pic-feedback.md
```

`--pic-command` is trusted local operator configuration. Do not let OpenClaw or an LLM generate it.

## What this release does not do

- It does not execute proposed OpenClaw actions.
- It does not run commands contained in action proposals.
- It does not clone or install PIC automatically.
- It does not call cloud LLMs.
- It does not prove correctness, real ASI, external-world truth, or action safety.
- It does not replace OpenClaw sandboxing, approvals, allowlists, or tool policy.
- It is not an automatic OpenClaw hook and not an OpenClaw core patch.
- It is not automatically published to ClawHub.

## ClawHub bundle

A minimal ClawHub submission bundle is included at `clawhub/pic-residual-guard/`.

The bundle is intentionally skill-only and MIT-0. The repository root remains Apache-2.0.

## Verification commands

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src scripts
uv run pytest
uv build
```

## Known limitations

- Not an OpenClaw core patch.
- Not an automatic hook.
- Not automatically published to ClawHub.
- No guarantee of OpenClaw Git skill install syntax across OpenClaw versions.
- PIC-backed mode requires trusted local user configuration.
- Does not replace sandboxing, user approval, or allowlists.
