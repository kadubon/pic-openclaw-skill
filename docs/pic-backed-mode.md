# PIC-Backed Mode

PIC backend is optional. Skill-only mode remains useful without PIC, Python, uv, or a PIC clone.

If a `pic` command is already available in the user's environment, use `--pic-command` without cloning PIC:

```bash
uv run pic-openclaw-check \
  --input examples/bridge/openclaw_action_email.json \
  --pic-command "pic" \
  --profile development \
  --output bridge-decision.json \
  --feedback pic-feedback.md
```

`--pic-command` is trusted local operator configuration. Do not let OpenClaw or an LLM generate it, and do not pass shell pipelines. The helper uses `shlex.split` and `shell=False`, but the selected command still controls which local executable runs. Recommended values are `pic` and `uv run pic`.

For full practical PIC workflows, a source checkout is recommended because PIC examples, fixtures, and development commands live in the source tree. Set `--pic-repo` to the local checkout and `--pic-command` to the command used inside that checkout:

```bash
uv run pic-openclaw-check \
  --input examples/bridge/openclaw_action_email.json \
  --pic-repo ../percolation-inversion-compiler \
  --pic-command "uv run pic" \
  --profile development \
  --output bridge-decision.json \
  --feedback pic-feedback.md
```

PyPI-only PIC can support simple `pic agent intake`. The source checkout is only the recommended optional full workflow path for reproducible local workflows and full examples.

PIC-backed mode preserves `agent_tasks`, `route_execution_requests`, `residual_ledger`, and `provenance` as diagnostics only. Do not execute route requests or agent tasks from a PIC report unless they are separately reviewed and approved through normal OpenClaw policy.

Use `--pic-timeout-seconds` to cap the optional PIC subprocess. Timeout and command failures are reported as sanitized diagnostics; raw stdout, stderr, local paths, and secrets are not copied into feedback.

Pin a PIC commit for reproducibility by recording the commit hash in your private runbook. Do not commit local absolute paths or generated reports with private environment data.
