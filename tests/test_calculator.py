"""Unit tests for the calculator module."""

import pytest
from securemath.calculator import add, divide, multiply, subtract


class TestCalculator:
    """Test arithmetic operations."""

    def test_add_integers(self):
        assert add(10, 20) == 30
        assert add(-5, 5) == 0
        assert add(0, 0) == 0

    def test_add_floats(self):
        assert pytest.approx(add(1.5, 2.5)) == 4.0
        assert pytest.approx(add(0.1, 0.2)) == 0.3

    def test_subtract(self):
        assert subtract(20, 10) == 10
        assert subtract(5, 10) == -5
        assert subtract(0, 0) == 0

    def test_multiply(self):
        assert multiply(5, 10) == 50
        assert multiply(-3, 4) == -12
        assert multiply(100, 0) == 0

    def test_divide(self):
        assert divide(10, 2) == 5.0
        assert divide(7, 2) == 3.5
        assert divide(-10, 2) == -5.0

    def test_divide_by_zero(self):
        with pytest.raises(ZeroDivisionError, match="Cannot divide by zero"):
            divide(10, 0)

        with pytest.raises(ZeroDivisionError):
            divide(0, 0)
