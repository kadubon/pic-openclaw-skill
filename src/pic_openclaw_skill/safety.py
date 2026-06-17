"""Shared safety helpers."""

from __future__ import annotations

import re
from pathlib import PurePosixPath, PureWindowsPath

SAFETY_BOUNDARY = [
    "Generated agent output is a candidate, not verified work.",
    "This report does not prove correctness, real ASI, external-world truth, or action safety.",
    "This report does not execute the proposed action.",
    "This checker does not run commands proposed by an agent.",
    "PIC accepted=true is not permission to execute.",
    "settled=false is diagnostic, not a command failure.",
]

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|token|secret|password|private[_-]?key)\s*[:=]\s*\S+"),
    re.compile(r"-----BEGIN [A-Z ]*" + "PRIVATE" + r" KEY-----"),
]

WINDOWS_ABS_RE = re.compile(r"\b[A-Za-z]:[\\/][^\s)>\]]+")
UNC_RE = re.compile(r"\\\\[^\s\\]+\\[^\s]+")
POSIX_ABS_RE = re.compile(r"(?<![\w:])/(?:Users|home|tmp|var|etc|mnt|workspace)/[^\s)>\]]+")


def sanitize_public_text(text: object) -> str:
    """Remove local paths and obvious secrets from user-facing text."""

    value = "" if text is None else str(text)
    value = WINDOWS_ABS_RE.sub("<local-path>", value)
    value = UNC_RE.sub("<local-path>", value)
    value = POSIX_ABS_RE.sub("<local-path>", value)
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("<secret-redacted>", value)
    return value


def safe_ref(path: str) -> str:
    """Return a public-safe path reference."""

    if WINDOWS_ABS_RE.search(path) or UNC_RE.search(path) or POSIX_ABS_RE.search(path):
        name = PureWindowsPath(path).name or PurePosixPath(path).name
        return name or "<input>"
    return sanitize_public_text(path)
