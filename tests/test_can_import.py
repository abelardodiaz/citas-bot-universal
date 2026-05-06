"""Smoke test: verify the package can be imported and exposes a version."""

import citas_bot


def test_package_imports() -> None:
    assert citas_bot is not None


def test_version_is_present() -> None:
    assert hasattr(citas_bot, "__version__")
    assert isinstance(citas_bot.__version__, str)
    assert citas_bot.__version__ != ""
