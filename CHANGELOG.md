# Changelog

## v0.1.0

Initial public release of PIC OpenClaw Skill.

### Added

- OpenClaw `PIC Residual Guard` skill.
- Skill-only advisory mode that requires no PIC, Python, uv, network access, or PIC clone.
- Optional PIC-backed helper CLI for users with a trusted local `pic` command or PIC source checkout.
- Deterministic OpenClaw action proposal, result claim, memory write, and skill install records.
- Conservative allow / warn / defer / block decision policy.
- `observe`, `advisory`, and `enforce` modes.
- Sanitized Markdown feedback generation.
- Optional PIC diagnostic extraction for `accepted`, `operationally_usable`, `settled`, missing obligations, residual summaries, agent tasks, route requests, residual ledgers, and provenance refs.
- Security boundary documentation.
- Threat model documentation.
- Publication checklist.
- Licensing notes.
- CI with ruff, format check, mypy, pytest, and build.

### Safety boundary

- Does not execute proposed OpenClaw actions.
- Does not run proposed shell commands.
- Does not clone or install PIC automatically.
- Does not prove correctness, real ASI, external-world truth, or action safety.
- Does not replace OpenClaw sandboxing, approvals, allowlists, or tool policy.
