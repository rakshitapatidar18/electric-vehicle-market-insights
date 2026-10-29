"""
Test Environment & Configuration Setup.
Verifies that essential libraries and paths are properly configured.
"""

import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config


def test_python_version():
    """Verify Python version is 3.10 or higher."""
    assert sys.version_info >= (3, 10), f"Python 3.10+ required, found {sys.version}"


def test_required_libraries_imported():
    """Verify core packages can be imported."""
    import pandas as pd
    import numpy as np
    import flask
    import plotly
    import sqlite3

    assert pd is not None
    assert np is not None
    assert flask is not None
    assert plotly is not None
    assert sqlite3 is not None


def test_directory_structure():
    """Verify all key directories exist."""
    assert config.BASE_DIR.exists()
    assert config.RAW_DATA_DIR.exists()
    assert config.PROCESSED_DATA_DIR.exists()
    assert config.DATABASE_DIR.exists()
    assert (config.BASE_DIR / "src").exists()
    assert (config.BASE_DIR / "templates").exists()
    assert (config.BASE_DIR / "static").exists()
    assert (config.BASE_DIR / "reports").exists()
    assert (config.BASE_DIR / "tests").exists()
