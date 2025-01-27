from functools import partial, reduce, lru_cache
from typing import List

# 1. Partial: Create a new function with some arguments already pre-filled
def power(base, exponent):
    return base ** exponent

# Create a square function by fixing the exponent to 2
square = partial(power, exponent=2)
print(f"Square of 3: {square(3)}")  # Output: 9

# Create a cube function by fixing the exponent to 3
cube = partial(power, exponent=3)
print(f"Cube of 4: {cube(4)}")  # Output: 64

# 2. Reduce: Aggregate elements in a list (or iterable) using a binary function
numbers = [1, 2, 3, 4, 5]
sum_numbers = reduce(lambda x, y: x + y, numbers)
print(f"Sum of numbers: {sum_numbers}")  # Output: 15

product_numbers = reduce(lambda x, y: x * y, numbers)
print(f"Product of numbers: {product_numbers}")  # Output: 120

# 3. Map: Apply a function to every element in a list (or iterable)
nums = [1, 2, 3, 4]
squared_numbers = list(map(lambda x: x**2, nums))
print(f"Squared numbers: {squared_numbers}")  # Output: [1, 4, 9, 16]

# Using map with a regular function
def double(x):
    return x * 2

doubled_numbers = list(map(double, nums))
print(f"Doubled numbers: {doubled_numbers}")  # Output: [2, 4, 6, 8]

# 4. Filter: Filter elements in a list (or iterable) based on a condition
even_numbers = list(filter(lambda x: x % 2 == 0, nums))
print(f"Even numbers: {even_numbers}")  # Output: [2, 4]

# Using filter with a regular function
def is_odd(x):
    return x % 2 != 0

odd_numbers = list(filter(is_odd, nums))
print(f"Odd numbers: {odd_numbers}")  # Output: [1, 3]

# 5. LRU Cache: Cache results of expensive function calls
@lru_cache(maxsize=32)
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(f"Fibonacci(10): {fibonacci(10)}")  # Output: 55
print(f"Fibonacci(20): {fibonacci(20)}")  # Output: 6765

# Cache statistics
print(f"Cache Info: {fibonacci.cache_info()}")

# 6. Combining everything: A more complex example
# Find the product of squares of even numbers in the list
even_squares = map(lambda x: x**2, filter(lambda x: x % 2 == 0, numbers))
product_even_squares = reduce(lambda x, y: x * y, even_squares)
print(f"Product of squares of even numbers: {product_even_squares}")
