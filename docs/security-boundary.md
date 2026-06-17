# Security Boundary

Generated agent output is a candidate, not verified work.

- This skill does not execute proposed actions.
- This skill does not run proposed shell commands.
- This skill does not clone PIC automatically.
- This skill does not install PIC automatically.
- This skill does not prove correctness.
- This skill does not prove real ASI.
- This skill does not validate external-world truth.
- PIC reports are diagnostic artifacts.
- Users remain responsible for action approval.

This skill is not a replacement for OpenClaw sandboxing, approval prompts, allowlists, or tool policy. OpenClaw is designed around a single-operator trust boundary; do not treat one shared gateway or agent as a hostile multi-tenant security boundary.

Recommended OpenClaw-side controls:

- run `openclaw security audit` after configuration changes
- keep exec on deny or ask for agents that do not need shell access
- keep filesystem tools workspace-only
- use skill allowlists for agents that should not see this skill

`--pic-command` is trusted local operator configuration. Do not let OpenClaw or an LLM generate it, and do not pass shell pipelines. The helper uses `shlex.split` with `shell=False`, but the command still selects a trusted local executable.

Do not include secrets, tokens, private keys, local absolute paths, browser profiles, or private OpenClaw workspace data in public examples or reports.
