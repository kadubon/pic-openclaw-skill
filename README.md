# PIC OpenClaw Skill

Residual-aware action checks for OpenClaw agents.

PIC OpenClaw Skill helps OpenClaw agents treat planned actions, result claims, memory writes, and skill installs as candidate work rather than verified work. It provides a lightweight OpenClaw skill for action-risk review and an optional PIC-backed checker for users who already have access to Percolation Inversion Compiler.

Generated agent output is a candidate, not verified work.

This skill does not clone PIC automatically.
This skill does not install PIC automatically.
This skill does not execute OpenClaw actions.
This skill does not run commands proposed by an agent.
PIC integration is optional and user-configured.

## What problem this solves

OpenClaw agents can draft shell commands, file writes, network requests, emails, memory writes, and skill installs faster than a human can verify them. This OpenClaw skill adds an autonomous agent guardrail: before an external-effect action is treated as work done, the agent records an agent action proposal, evidence, proof obligations, rollback path, and risk level.

The goal is AI agent action checking, AI workflow verification, LLM output validation, and residual ledger preservation. It is not a generic multi-agent bridge and it is not an action executor.

## Quick start: skill-only mode

Skill-only mode is the default path. It does not require PIC, Python, uv, a network call, or a clone of the PIC repository.

Install directly from this public repository when your OpenClaw environment allows Git skill installs:

```bash
openclaw skills install git:kadubon/pic-openclaw-skill@main
```

Or copy the skill directory into the workspace skill root:

```bash
mkdir -p <workspace>/skills/pic-residual-guard
cp -R skill/pic-residual-guard/* <workspace>/skills/pic-residual-guard/
```

Use `~/.openclaw/skills/pic-residual-guard` only when you want a shared managed skill visible across local agents. Then ask OpenClaw to use the PIC Residual Guard before external-effect actions. Skill-only mode needs only `skill/pic-residual-guard/SKILL.md` and the examples in that directory.

## Optional: PIC-backed mode

The helper CLI is optional. Use it when you want deterministic JSON decisions and feedback markdown. The recommended helper environment uses uv, matching PIC's development workflow:

```bash
uv sync --all-extras --dev
uv run pic-openclaw-check \
  --input examples/bridge/openclaw_action_email.json \
  --output bridge-decision.json \
  --feedback pic-feedback.md
```

PIC-backed mode is optional and can use an existing `pic` command without cloning PIC:

```bash
uv run pic-openclaw-check \
  --input examples/bridge/openclaw_action_email.json \
  --pic-command "pic" \
  --profile development \
  --output bridge-decision.json \
  --feedback pic-feedback.md
```

For full practical PIC workflows, reproducibility, and repository fixtures, a local PIC source checkout is recommended but not required:

```bash
git clone https://github.com/kadubon/percolation-inversion-compiler.git
cd percolation-inversion-compiler
uv sync --all-extras --dev
```

Then run the helper from this repository:

```bash
uv run pic-openclaw-check \
  --input examples/bridge/openclaw_action_email.json \
  --mode advisory \
  --pic-repo ../percolation-inversion-compiler \
  --pic-command "uv run pic" \
  --profile development \
  --output bridge-decision.json \
  --feedback pic-feedback.md
```

The checker renders the OpenClaw proposal as candidate text and may run:

```bash
uv run pic agent intake --text-file <candidate-text> --profile development --output <pic-report>
```

It does not execute the proposed OpenClaw action.

## What counts as an external-effect action

External-effect actions include shell command, file write, file delete, network request, email send, message send, calendar edit, package install, skill install, repository mutation, persistent memory write, credential or token handling, browser automation, payment, purchase, and irreversible transaction.

## Action proposal format

Use `OpenClawActionProposal` for pre-action checks. It records the proposed tool, arguments as data, evidence refs, missing evidence, rollback plan, risk level, and whether human confirmation is required. See `schemas/openclaw-action-proposal.schema.json`.

## Result claim format

Use `OpenClawResultClaim` when an agent claims work completed. The checker asks for evidence refs, log refs, rollback availability, and unresolved items. A completion claim without logs or evidence remains candidate work.

## Memory write check

Use `OpenClawMemoryWrite` before persistent memory writes. Unsupported factual claims without evidence defer by default. Preference or plan memories can still warn or defer depending on persistence and risk.

## Skill install check

Use `OpenClawSkillInstall` before installing an OpenClaw skill. Skill install safety requires clear source, requested permissions, install steps, and explicit review when shell, network, file writes, or credential access are involved.

## Decision meanings

- `allow`: low-risk action with adequate evidence and reversible effects.
- `warn`: low or medium risk action with residuals that can be safely carried forward.
- `defer`: missing evidence, missing rollback plan, missing user confirmation, or external-effect action that needs review.
- `block`: credential exposure, unsafe shell, destructive file operation, unauthorized network action, skill install with unclear permissions, or any critical risk action without explicit user approval.

`allowed_to_execute` is false unless the bridge policy says the action can proceed. PIC `accepted=true` is diagnostic input, not permission to execute.

## Security boundary

This repository is an OpenClaw agent safety helper. It does not clone PIC automatically, install PIC automatically, execute OpenClaw actions, run commands proposed by an agent, create PRs, create issues, mutate repositories, access credentials, or call cloud LLMs.

This skill is not a replacement for OpenClaw sandboxing, approvals, allowlists, or tool policy. Run `openclaw security audit`, keep exec on deny or ask where appropriate, keep filesystem tools workspace-only, and use skill allowlists for agents that should not see this skill.

Feedback output is sanitized to avoid local absolute paths and secrets. Generated agent output is a candidate, not verified work.

## ClawHub note

This repository is Apache-2.0. ClawHub-published skills are documented by OpenClaw as MIT-0, so ClawHub publication requires a separate license decision. This repository intentionally documents Git/local skill installation and does not include registry publication steps.

## Relationship to Percolation Inversion Compiler

PIC integration is optional and user-configured. PIC is used as a residual ledger and proof obligation diagnostic for candidate text. This repository reads PIC fields such as `accepted`, `operationally_usable`, `settled`, `missing_obligations`, `residual_summary`, `residual_ledger`, `agent_tasks`, `route_execution_requests`, and `provenance` when a PIC command is configured. PIC tasks and route requests are diagnostic only; they are not execution instructions.

This skill does not claim that PIC proves real ASI, external-world truth, or action safety.

Search terms: OpenClaw skill, OpenClaw agent safety, AI agent action checking, AI workflow verification, autonomous agent guardrail, LLM output validation, residual ledger, proof obligations, agent action proposal, skill install safety, memory write review, PIC integration, Percolation Inversion Compiler.

## Examples

Examples live in `examples/bridge/` and `skill/pic-residual-guard/examples/`.

```bash
uv run pic-openclaw-check \
  --input examples/bridge/openclaw_action_shell.json \
  --output bridge-decision.json \
  --feedback pic-feedback.md
```

## Tests

```bash
uv sync --all-extras --dev
uv run pytest
uv run ruff check .
uv run mypy src scripts
```

Tests do not require PIC, do not clone PIC, do not run OpenClaw, do not require network, and do not run shell commands from example action proposals.

## License

Apache-2.0. See `LICENSE`.
