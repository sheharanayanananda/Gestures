"""One Euro Filter for jitter-free real-time cursor tracking.

Reference:
    Casiez, G., Roussel, N. and Vogel, D. (2012).
    1 € Filter: A Simple Speed-based Low-pass Filter for Noisy Input in Interactive Systems.
    CHI '12.
"""
import math
import time


class LowPassFilter:
    """Standard exponential smoothing low-pass filter."""

    def __init__(self, alpha: float = 1.0):
        self.alpha = alpha
        self.last_val = None

    def filter(self, value: float, alpha: float = None) -> float:
        if alpha is not None:
            self.alpha = alpha
        if self.last_val is None:
            self.last_val = value
            return value
        filtered = self.alpha * value + (1.0 - self.alpha) * self.last_val
        self.last_val = filtered
        return filtered

    def reset(self):
        self.last_val = None


class OneEuroFilter:
    """1€ Filter for 1D or scalar signals."""

    def __init__(
        self,
        min_cutoff: float = 1.0,
        beta: float = 0.05,
        d_cutoff: float = 1.0,
    ):
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)
        self.x_filter = LowPassFilter()
        self.dx_filter = LowPassFilter()
        self.last_time = None

    def _alpha(self, rate: float, cutoff: float) -> float:
        tau = 1.0 / (2.0 * math.pi * cutoff)
        te = 1.0 / rate
        return 1.0 / (1.0 + tau / te)

    def filter(self, x: float, timestamp: float = None) -> float:
        if timestamp is None:
            timestamp = time.perf_counter()

        if self.last_time is None:
            self.last_time = timestamp
            return self.x_filter.filter(x, 1.0)

        dt = timestamp - self.last_time
        self.last_time = timestamp

        # Guard against zero or negative dt
        if dt <= 1e-6:
            dt = 1e-3
        rate = 1.0 / dt

        # Estimate derivative of the signal
        prev_x = self.x_filter.last_val if self.x_filter.last_val is not None else x
        dx = (x - prev_x) * rate
        edx = self.dx_filter.filter(dx, self._alpha(rate, self.d_cutoff))

        # Dynamic cutoff frequency based on speed
        cutoff = self.min_cutoff + self.beta * abs(edx)
        return self.x_filter.filter(x, self._alpha(rate, cutoff))

    def reset(self):
        self.x_filter.reset()
        self.dx_filter.reset()
        self.last_time = None


class PointFilter2D:
    """2D wrapper running two 1€ filters for (x, y) coordinates."""

    def __init__(
        self,
        min_cutoff: float = 1.2,
        beta: float = 0.05,
        d_cutoff: float = 1.0,
    ):
        self.filter_x = OneEuroFilter(min_cutoff=min_cutoff, beta=beta, d_cutoff=d_cutoff)
        self.filter_y = OneEuroFilter(min_cutoff=min_cutoff, beta=beta, d_cutoff=d_cutoff)

    def filter(self, x: float, y: float, timestamp: float = None) -> tuple:
        fx = self.filter_x.filter(x, timestamp=timestamp)
        fy = self.filter_y.filter(y, timestamp=timestamp)
        return (fx, fy)

    def reset(self):
        self.filter_x.reset()
        self.filter_y.reset()
