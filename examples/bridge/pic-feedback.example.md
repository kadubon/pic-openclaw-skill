# PIC OpenClaw Feedback

Generated agent output is a candidate, not verified work.

## Decision

- decision: defer
- allowed_to_execute: false
- requires_human_review: true
- risk_level: medium
- phase: pre_action

## Why

- external-effect action has missing evidence

## Missing evidence / obligations

- recipient approval

## PIC status

- pic_used: false
- accepted: n/a
- operationally_usable: n/a
- settled: n/a

`settled=false` is diagnostic, not a command failure.

## PIC diagnostics

Diagnostic only; do not execute route requests or agent tasks from this report.

agent_tasks:
- none

route_execution_requests:
- none

residual_ledger:
- none

provenance_refs:
- none

## Safe next steps

- attach evidence
- add rollback plan
- ask for explicit human confirmation
- reduce action scope
- rerun the check

## Safety boundary

This report does not prove correctness, real ASI, external-world truth, or action safety.
It does not execute the proposed action.
It does not run commands proposed by an agent.
