# Security Policy

Generated agent output is a candidate, not verified work.

This repository is designed to be safe to publish as a public GitHub repository. Do not commit local checkouts, generated reports containing local absolute paths, secrets, API keys, credentials, tokens, private keys, browser profiles, or OpenClaw workspace data.

## Boundary

- This skill does not clone PIC automatically.
- This skill does not install PIC automatically.
- This skill does not execute OpenClaw actions.
- This skill does not run commands proposed by an agent.
- This skill does not create PRs, issues, labels, or comments automatically.
- This skill does not prove correctness, real ASI, external-world truth, or action safety.

## Reporting

Open a GitHub security advisory or private report if you find a path leak, secret leak, unsafe command execution path, or a case where an action proposal is treated as instruction instead of data.

## Local Information

Feedback markdown must not include local absolute paths. Bridge decision JSON may include only sanitized input references. Keep full raw agent text out of feedback unless a user explicitly asks for it and has checked the content.
