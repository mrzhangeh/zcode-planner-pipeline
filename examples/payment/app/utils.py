"""Shared helpers."""


def constant_time_equal(a: str, b: str) -> bool:
    """Length-safe constant-time string comparison."""
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0
