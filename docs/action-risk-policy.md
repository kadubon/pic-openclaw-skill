# Action Risk Policy

Decisions are deterministic.

- Critical risk blocks unless explicit human confirmation exists and no credential, shell, destructive, or unresolved hazard remains.
- High risk defers by default.
- External effect plus no rollback plan defers.
- External effect plus missing evidence defers.
- Credential access blocks.
- Skill install with unclear permissions defers or blocks.
- Shell required with unknown command blocks.
- PIC command failure defers in observe/advisory mode and blocks in enforce mode.
- PIC `settled=false` means review is incomplete, not command failure.
- PIC `accepted=true` is not permission to execute.
- PIC `operationally_usable=false` preserves unresolved work and defers high-risk actions.
- Low risk with no external effect warns or allows depending on missing evidence.
- Memory write with unsupported factual claim defers.
