import os

import pytest

from fontbuild.build_font import build

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def base_font_path() -> str:
    """Absolute path to the static Jost base font, cwd-independent."""
    return os.path.join(ROOT, "base", "Jost-Regular.ttf")


@pytest.fixture(scope="session")
def built_font_path() -> str:
    """Build the font once per test session and return its path."""
    out = os.path.join(ROOT, "dist", "SoulsOnly.ttf")
    build()
    assert os.path.exists(out)
    return out


@pytest.fixture(scope="session")
def built_vf_path(built_font_path) -> str:
    """Build the variable reveal font once (after the aligned font exists)."""
    from fontbuild.reveal import OUT_VF, build_reveal

    build_reveal()
    assert os.path.exists(OUT_VF)
    return OUT_VF
