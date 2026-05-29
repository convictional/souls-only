import os

import pytest

from fontbuild.build_font import build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def built_font_path() -> str:
    """Build the font once per test session and return its path."""
    out = os.path.join(ROOT, "dist", "SoulsOnly.ttf")
    build()
    assert os.path.exists(out)
    return out
