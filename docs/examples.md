# Examples

Examples in `examples/bridge/` cover email, shell, file write, result claim, memory write, and skill install checks.

Run skill-only mode:

```bash
uv run pic-openclaw-check --input examples/bridge/openclaw_action_email.json
```

The helper CLI defaults to skill-only advisory mode. Use `--pic-command` only when an existing PIC command is available, and use `--pic-repo` only for the optional full workflow source checkout.

Generated agent output is a candidate, not verified work.
