# Release v0.2.0

PIC OpenClaw Skill is a review-first action checking skill for OpenClaw agents.

Generated agent output is a candidate, not verified work.

This release updates the skill and helper for current PIC agent check reports while keeping the default OpenClaw path simple: skill-only mode still works without PIC, Python, uv, network access, or a PIC clone.

## What this release provides

- A clearer OpenClaw `PIC Residual Guard` skill written in general terms for agents.
- Skill-only mode for manual OpenClaw installation.
- Optional helper CLI with deterministic JSON decisions and Markdown feedback.
- Current PIC-backed mode using `pic agent check --compact` by default.
- Optional legacy PIC-backed mode with `--pic-entrypoint agent-intake`.
- Review-only handling for PIC fields such as `workflow_usable`, `next_safe_actions`, `agent_tasks`, and `route_execution_requests`.
- Sanitized feedback that avoids local absolute paths and obvious secret patterns.
- ClawHub bundle metadata using general search terms for action review, agent safety, workflow verification, and LLM output validation.

## Recommended first use

Start with manual skill-only install:

```bash
mkdir -p <workspace>/skills/pic-residual-guard
cp -R skill/pic-residual-guard/* <workspace>/skills/pic-residual-guard/
```

Then review `SKILL.md` and ask OpenClaw to use the PIC Residual Guard before external-effect actions.

## Optional PIC-backed mode

PIC-backed mode is optional. Use it only when you have reviewed the skill and have a trusted local PIC command:

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
- No guarantee of OpenClaw Git skill install syntax across OpenClaw versions.
- PIC-backed mode requires trusted local user configuration.
- Does not replace sandboxing, user approval, or allowlists.
