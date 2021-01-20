"""Module to aid with data validation"""


def assert_positive_number(n, name):
    """Assert that an input is a positive number."""
    if type(n) not in [int, float]:
        raise ValueError(
            f"The value for '{name}' should be an integer or a float, not a {type(n)}.")
    if n < 0:
        raise ValueError(
            f"The value for '{name}' should be >= 0, not {n}")

def assert_strictly_positive_number(n, name):
    """Assert that an input is a strictly positive number."""
    if type(n) not in [int, float]:
        raise ValueError(
            f"The value for '{name}' should be an integer or a float, not a {type(n)}.")
    if n < 0:
        raise ValueError(
            f"The value for '{name}' should be > 0, not {n}")


def assert_number(n, name):
    """Assert that an input is a number."""
    if type(n) not in [int, float]:
        raise ValueError(
            f"The value for '{name}' should be an integer or a float, not a {type(n)}.")
