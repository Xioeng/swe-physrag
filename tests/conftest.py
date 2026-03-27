"""
Pytest configuration and shared fixtures for test suite.
"""

import matplotlib
import pytest

# Use non-interactive backend for tests
matplotlib.use("Agg")
