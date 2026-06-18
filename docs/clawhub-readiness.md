# ClawHub / Registry Readiness

This repository is prepared for manual GitHub-based installation and a separate manual ClawHub submission path. It is not automatically published to ClawHub.

ClawHub or registry submission should happen only after verifying current registry requirements. The commands below are manual operator commands and are not CI steps.

The skill must remain no-auto-clone, no-auto-install, and no-action-execution.

## Current ClawHub preparation

This repository now contains a minimal ClawHub submission bundle:

`clawhub/pic-residual-guard/`

The repository root remains Apache-2.0.
The ClawHub submission bundle is MIT-0.

Submit the ClawHub bundle directory, not the repository root.

## Manual dry run

Do not run this in CI. Run it only after installing and authenticating the ClawHub CLI in a trusted local operator environment.

```bash
clawhub skill publish clawhub/pic-residual-guard \
  --slug pic-residual-guard \
  --name "PIC Residual Guard" \
  --version 0.1.0 \
  --changelog "Initial public release: residual-aware action checks for OpenClaw agents." \
  --dry-run
```

## Manual publish

Run this only after the dry run output and current ClawHub requirements have been reviewed.

```bash
clawhub skill publish clawhub/pic-residual-guard \
  --slug pic-residual-guard \
  --name "PIC Residual Guard" \
  --version 0.1.0 \
  --changelog "Initial public release: residual-aware action checks for OpenClaw agents."
```

## Manual post-publish checks

These checks require ClawHub and OpenClaw operator tooling. They are not CI steps.

```bash
clawhub inspect pic-residual-guard --versions --files
clawhub inspect pic-residual-guard --json
openclaw skills install pic-residual-guard
openclaw skills verify pic-residual-guard
openclaw skills verify pic-residual-guard --card
```

## Checklist

- [ ] verify current registry submission requirements
- [ ] verify license requirements
- [ ] verify `clawhub/pic-residual-guard/SKILL.md` is accepted
- [ ] confirm no install scripts are required
- [ ] confirm no secret, credential, or local path appears in examples
- [ ] confirm manual dry run succeeds
- [ ] confirm manual post-publish install and verify commands work after publication
