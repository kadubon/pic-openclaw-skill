# Changelog

## v0.2.0

OpenClaw and ClawHub update focused on current PIC agent reports, plain-language agent instructions, and clearer search metadata.

### Added

- Current PIC `pic agent check --compact` helper path.
- Review-only preservation for `workflow_usable`, unresolved items, suggested review items, schema refs, safety rules, checked outputs, agent tasks, route requests, and source refs.
- Plain-language alignment notes for agents.
- ClawHub v0.2.0 publish metadata with general search terms.

### Changed

- Skill and README language now describes review-first action checks instead of theory-specific wording.
- PIC source checkout remains optional; installed `pic` and skill-only mode stay supported.
- PIC report fields are treated as review data only and never as OpenClaw execution authority.
- ClawHub bundle description and README use general terms for action review, risk checks, rollback planning, and LLM output validation.

### Safety boundary

- Does not execute proposed OpenClaw actions.
- Does not run proposed shell commands.
- Does not clone or install PIC automatically.
- Does not prove correctness, real ASI, external-world truth, or action safety.
- Does not replace OpenClaw sandboxing, approvals, allowlists, or tool policy.

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
- Optional PIC review data extraction for `accepted`, `operationally_usable`, `settled`, missing checks, summary data, agent tasks, route requests, unresolved-work notes, and source refs.
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
