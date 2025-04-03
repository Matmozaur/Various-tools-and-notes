import pytest

@pytest.mark.parametrize(
    "a, b, expected",
    [(2, 3, 5), (-1, 1, 0), (0, 0, 0)]
)
def test_addition(calculator, a, b, expected):
    """Parameterized test for addition."""
    assert calculator.add(a, b) == expected

def test_divide_by_zero(calculator):
    """Test that division by zero raises an error."""
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        calculator.divide(10, 0)

@pytest.mark.slow
def test_slow_operation(calculator):
    """Custom marker: Slow tests can be skipped selectively."""
    import time
    time.sleep(2)
    assert calculator.multiply(2, 2) == 4

# def test_mocking(mocker, calculator):
#     """Using pytest-mock to mock a function."""
#     mocker.patch.object(calculator, 'add', return_value=100)
#     assert calculator.add(10, 5) == 100
