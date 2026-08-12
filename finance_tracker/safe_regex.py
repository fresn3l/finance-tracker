"""Guards for user-supplied regular expressions (ReDoS)."""

from __future__ import annotations

import re
from typing import Pattern

MAX_PATTERN_LENGTH = 160
# Group that already has a quantifier, then another quantifier: (a+)+
_NESTED_GROUP = re.compile(r"\([^)]*[*+{][^)]*\)[*+?{]")
# Repeated wildcard quantifiers: .*.* or .+.+
_STACKED_WILDCARDS = re.compile(r"(\.\*){2,}|(\.\+){2,}")


def compile_user_regex(pattern: str, case_sensitive: bool = False) -> Pattern[str]:
    """
    Compile a user-supplied regex after rejecting empty, huge, or nested-quantifier patterns.
    """
    if not isinstance(pattern, str) or not pattern.strip():
        raise ValueError("Pattern is required")
    if len(pattern) > MAX_PATTERN_LENGTH:
        raise ValueError(f"Pattern is too long (max {MAX_PATTERN_LENGTH} characters)")
    if _NESTED_GROUP.search(pattern) or _STACKED_WILDCARDS.search(pattern):
        raise ValueError("Pattern has nested quantifiers")
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(pattern, flags)
