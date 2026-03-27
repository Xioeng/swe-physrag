#!/usr/bin/env python
"""
Legacy setup script for backward compatibility.

New projects should use pyproject.toml instead. This file exists for
compatibility with older pip/setuptools versions.

For development install: pip install -e .
For all extras: pip install -e ".[all]"
For tidalflow integration: pip install -e ".[tidalflow]"
"""

from setuptools import setup

setup()
