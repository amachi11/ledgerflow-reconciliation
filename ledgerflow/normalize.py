"""Reusable normalization rules for reconciliation signals."""
import re

_NOISE_WORDS = {"a", "an", "and", "the", "of", "for", "on", "at", "payment", "transfer"}


def normalize_reference(value: str) -> str:
    """Remove separators/casing; preserve letters and digits."""
    return "".join(char for char in value.upper() if char.isalnum())


def description_tokens(value: str) -> set[str]:
    return {
        token for token in re.findall(r"[a-z0-9]+", value.lower())
        if token not in _NOISE_WORDS
    }


def description_similarity(left: str, right: str) -> float:
    """Jaccard overlap between meaningful description tokens."""
    a, b = description_tokens(left), description_tokens(right)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
