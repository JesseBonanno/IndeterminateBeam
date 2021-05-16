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


def assert_length(l, num, name):
    """Assert that a tuple or list is of a specific length."""
    if len(l) != num:
        raise ValueError(
            f"The length of '{name}' should be {num} not {len(l)}.")

def assert_list_contents(l, content, name):
    """Assert that a tuple or list contains only specific items"""
    for a in l:
        if a not in content:
            raise ValueError(
                    f"The variable '{name}', must be a tuple or"+
                    f" list containing only items in {content} not {a}."
                )

def assert_contents(var, content, name):
    """Assert that a variable is within a specific subset of available values"""
    
    var = [var]
    for a in var:
        if a not in content:
            raise ValueError(
                    f"The variable '{name}', must only have a"+
                    f" value that is specified in {content} not '{a}'."
                )