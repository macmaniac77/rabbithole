"""Utility functions for mathematical operations."""


def factorial(n: int) -> int:
    """Compute the factorial of a non-negative integer using recursion.

    Args:
        n: Non-negative integer for which to compute the factorial.

    Returns:
        Factorial of n.

    Raises:
        ValueError: If n is negative.
    """
    if n < 0:
        raise ValueError("n must be a non-negative integer")
    if n in (0, 1):
        return 1
    return n * factorial(n - 1)
