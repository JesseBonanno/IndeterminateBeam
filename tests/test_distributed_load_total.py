"""Unit tests for _distributed_load_total function."""

import pytest
from indeterminatebeam.loading import UDL, TrapezoidalLoad
from indeterminatebeam.report import _distributed_load_total


class TestDistributedLoadTotalConstant:
    """Tests for constant (uniform) distributed loads (UDL)."""

    def test_udl_basic(self):
        """Test a UDL of 100 N/m from x=0 to x=5."""
        load = UDL(100, span=(0, 5), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "constant"
        assert w1 is not None
        assert abs(w1 - 100) < 1e-4
        assert w2 is None
        assert abs(total - 500) < 1e-4

    def test_udl_2000(self):
        """Test UDL with 2000 N/m from x=1 to x=4."""
        udl = UDL(2000, span=(1, 4), angle=90)
        load_type, w1, w2, total = _distributed_load_total(udl)

        assert load_type == "constant"
        assert w1 is not None
        assert abs(w1 - 2000) < 1e-4
        assert abs(total - 6000) < 1e-4

    def test_udl_zero(self):
        """Test zero UDL."""
        load = UDL(0, span=(0, 5), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "constant"
        assert abs(w1 - 0) < 1e-4
        assert abs(total - 0) < 1e-4

    def test_udl_negative(self):
        """Test negative (downward) UDL."""
        load = UDL(-1500, span=(2, 6), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "constant"
        assert abs(w1 - (-1500)) < 1e-4
        assert abs(total - (-6000)) < 1e-4

    def test_udl_large_span(self):
        """Test UDL with large span."""
        load = UDL(2500, span=(0, 100), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "constant"
        assert abs(w1 - 2500) < 1e-4
        assert abs(total - 250000) < 1e-4

    def test_udl_fractional(self):
        """Test UDL with fractional values."""
        load = UDL(0.5, span=(0, 10), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "constant"
        assert abs(w1 - 0.5) < 1e-4
        assert abs(total - 5) < 1e-4


class TestDistributedLoadTotalTrapezoidal:
    """Tests for trapezoidal (linearly varying) distributed loads."""

    def test_trapezoidal_increasing(self):
        """Test linearly increasing TrapezoidalLoad: w from 100 to 300 N/m from x=0 to x=4."""
        load = TrapezoidalLoad((100, 300), span=(0, 4), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "trapezoidal"
        assert w1 is not None
        assert w2 is not None
        assert abs(w1 - 100) < 1e-4
        assert abs(w2 - 300) < 1e-4
        assert abs(total - 800) < 1e-4

    def test_trapezoidal_decreasing(self):
        """Test linearly decreasing TrapezoidalLoad: w from 400 to 200 N/m from x=0 to x=4."""
        load = TrapezoidalLoad((400, 200), span=(0, 4), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "trapezoidal"
        assert abs(w1 - 400) < 1e-4
        assert abs(w2 - 200) < 1e-4
        assert abs(total - 1200) < 1e-4

    def test_trapezoidal_offset_span(self):
        """Test TrapezoidalLoad with offset span: w from 150 to 350 N/m from x=1 to x=3."""
        load = TrapezoidalLoad((150, 350), span=(1, 3), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "trapezoidal"
        assert abs(w1 - 150) < 1e-4
        assert abs(w2 - 350) < 1e-4
        assert abs(total - 500) < 1e-4

    def test_trapezoidal_standard(self):
        """Test TrapezoidalLoad: w from 100 to 400 N/m from x=0 to x=5."""
        tload = TrapezoidalLoad((100, 400), span=(0, 5), angle=90)
        load_type, w1, w2, total = _distributed_load_total(tload)

        assert load_type == "trapezoidal"
        assert abs(w1 - 100) < 1e-4
        assert abs(w2 - 400) < 1e-4
        assert abs(total - 1250) < 1e-4

    def test_trapezoidal_small_span(self):
        """Test TrapezoidalLoad with small span: w from 0 to 100 N/m from x=0 to x=0.1."""
        load = TrapezoidalLoad((0, 100), span=(0, 0.1), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "trapezoidal"
        assert abs(w1 - 0) < 1e-4
        assert abs(w2 - 100) < 1e-4
        assert abs(total - 5) < 1e-4

    def test_trapezoidal_negative(self):
        """Test negative TrapezoidalLoad."""
        load = TrapezoidalLoad((-100, -200), span=(0, 2), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "trapezoidal"
        assert abs(w1 - (-100)) < 1e-4
        assert abs(w2 - (-200)) < 1e-4
        assert abs(total - (-300)) < 1e-4


class TestDistributedLoadTotalEdgeCases:
    """Tests for edge cases with UDL and TrapezoidalLoad."""

    def test_udl_zero_span(self):
        """Test UDL with zero span (same start and end)."""
        load = UDL(100, span=(5, 5), angle=90)
        load_type, w1, w2, total = _distributed_load_total(load)

        # Zero span should result in zero total
        assert abs(total - 0) < 1e-4


class TestDistributedLoadTotalUnsupported:
    """Tests for unsupported load types."""

    def test_unsupported_type_returns_other(self):
        """Test that unsupported load types return 'other'."""
        from indeterminatebeam.loading import PointLoad

        # PointLoad is not a supported distributed load type
        load = PointLoad(-1000, 3, 90)
        load_type, w1, w2, total = _distributed_load_total(load)

        assert load_type == "other"
        assert w1 is None
        assert w2 is None
