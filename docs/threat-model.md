# Threat Model

Generated agent output is a candidate, not verified work.

Covered threats:

- prompt injection in action proposals
- malicious skill install
- unsafe shell command
- destructive file write or delete
- credential leakage
- unsupported memory write
- false completion claim
- overtrusting `accepted=true`
- misreading `settled=false`

Mitigations are advisory and deterministic: preserve missing obligations, block credential exposure, block unknown shell commands, defer missing evidence, and never execute proposed actions.

OpenClaw-side controls remain required. This skill does not replace sandboxing, approval prompts, tool policy, exec deny/ask settings, workspace-only filesystem policy, or skill allowlists.

Assume a single-operator trust boundary. If multiple mutually untrusted users can trigger one OpenClaw gateway or tool-enabled agent, split the deployment by gateway, OS user, host, or credential set instead of relying on this skill as isolation.
