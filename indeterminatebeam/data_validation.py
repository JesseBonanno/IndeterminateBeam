def assert_positive_number(n , name):
    if type(n) not in [int, float]:
            raise ValueError(f"{name} should be an integer or a float, not a {type(n)}")
    if n<0:
        raise ValueError(f"{name} should be greater than 0, not {n}")

def assert_number(n,name):
    if type(n) not in [int, float]:
        raise ValueError(f"{name} should be an integer or a float, not a {type(n)}")
