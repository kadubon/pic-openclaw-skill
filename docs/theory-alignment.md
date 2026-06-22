# Plain-Language Alignment

This repository uses the background theory files as a source of review rules.
Agents should not need special theory vocabulary to use the skill.

## Rules For Agents

- Treat generated agent output as candidate work, not completed work.
- Treat a possible action path as information about what might be done, not as
  permission to do it.
- Keep missing evidence visible as unresolved work.
- Keep rollback or undo information visible before external effects.
- Treat trace logs as records of observed behavior. They do not prove facts
  about the outside world.
- Treat error budgets as limits on a representation. They do not make an
  uncertain claim true.
- Treat suggested next steps as review notes. Do not run them without normal
  OpenClaw approval and tool policy.
- Preserve review bandwidth. A long list of suggestions can distract from the
  actual missing evidence.
- Treat a useful local result as reusable only after evidence, scope, authority,
  risk, maintenance, and final review checks pass.

## PIC Fields In Plain Language

- `accepted=true`: PIC accepted a scoped report shape or finite check. This is
  not execution approval.
- `workflow_usable=true`: the report is useful for the next review or planning
  step. This is not execution approval.
- `operationally_usable=true`: PIC considers the report more usable under its
  selected profile. OpenClaw still needs its own approvals and policy checks.
- `settled=false`: unresolved work remains. Do not claim final completion.
- `unresolved_obligations`: missing evidence, missing checks, or remaining
  review work.
- `next_safe_actions`: suggested review items from PIC. They are not commands.
- `agent_tasks`: task suggestions from PIC. They are not commands.
- `route_execution_requests`: requests to use a verifier route. They are not
  commands and do not authorize tool use.

## What This Skill Does Not Prove

This skill does not prove real ASI, external-world truth, physical safety,
legal compliance, policy compliance, action safety, or tool authorization. It
helps preserve evidence, unresolved work, rollback notes, and conservative
action decisions before OpenClaw external effects.
