import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture
def base_font_path() -> str:
    """Absolute path to the static Jost base font, cwd-independent."""
    return os.path.join(ROOT, "base", "Jost-Regular.ttf")


@pytest.fixture(scope="session")
def built_keys_path() -> str:
    """Build the keyboard-typeable static font once."""
    from fontbuild.build_keyboard import OUT_FONT, build

    build()
    assert os.path.exists(OUT_FONT)
    return OUT_FONT


@pytest.fixture(scope="session")
def built_keys_vf_path(built_keys_path) -> str:
    """Build the decoy reveal (REVL) font once."""
    from fontbuild.build_keyboard import OUT_FONT, OUT_VF
    from fontbuild.decoy_reveal import build_decoy_reveal

    build_decoy_reveal(aligned_path=OUT_FONT, out_vf=OUT_VF)
    assert os.path.exists(OUT_VF)
    return OUT_VF
