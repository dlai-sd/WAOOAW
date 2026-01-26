import math

def get_factorial(n):
    return str(math.factorial(n))
def get_factorial(n: int) -> int:
    """Calculate the factorial of a number."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers.")
    if n == 0:
        return 1
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result
