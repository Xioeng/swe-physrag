"""
Data interpolation module for sparse spatiotemporal measurements.

Provides interpolation and extrapolation methods for 2D data retrieved from
1-2 measurement stations, suitable for SWE model input generation.
"""

from .sparse_interpolator import SparseDataInterpolator

__all__ = ["SparseDataInterpolator"]
