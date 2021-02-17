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

def assert_length(var, num, name):
    """Assert that a tuple or list is of a specific length."""
    if len(var) != num:
        raise ValueError(
            f"The length of '{name}' should be {num} not {len(var)}.")
