"""The version lives in trading_agent/__init__.py and nowhere else.

pyproject reads it through setuptools' dynamic version and coinductor re-exports
it, but the Inno Setup script cannot import Python. This test is what stops that
last copy from drifting at release time.
"""

from pathlib import Path
import re
import tomllib

import coinductor
import trading_agent

_ROOT = Path(__file__).resolve().parent.parent


def test_desktop_package_reports_the_engine_version() -> None:
    assert coinductor.__version__ == trading_agent.__version__


def test_pyproject_reads_the_version_from_the_package() -> None:
    pyproject = tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "version" in pyproject["project"].get("dynamic", [])
    assert pyproject["tool"]["setuptools"]["dynamic"]["version"] == {
        "attr": "trading_agent.__version__"
    }


def test_installer_version_matches_the_package() -> None:
    script = (_ROOT / "packaging" / "coinductor.iss").read_text(encoding="utf-8")

    match = re.search(r'#define\s+AppVersion\s+"([^"]+)"', script)

    assert match is not None, "coinductor.iss no longer defines AppVersion"
    assert match.group(1) == trading_agent.__version__, (
        "packaging/coinductor.iss is out of step with trading_agent.__version__"
    )


def test_installer_clears_exactly_the_managed_credentials() -> None:
    """The uninstaller's key list cannot drift from the one the app writes.

    It is Pascal in an .iss file, so nothing else would catch a key added to
    MANAGED_KEYS but not here - and the failure mode is silent: a Binance
    secret left in the OS vault after the user asked for everything to go.
    """
    from coinductor.secret_store import MANAGED_KEYS

    script = (_ROOT / "packaging" / "coinductor.iss").read_text(encoding="utf-8")

    block = re.search(r"ManagedKeys\s*=(.*?);", script, re.DOTALL)
    assert block is not None, "coinductor.iss no longer defines ManagedKeys"
    listed = {key for key in re.findall(r"[A-Z_]{4,}", block.group(1))}

    assert listed == set(MANAGED_KEYS), (
        f"installer/app credential lists differ: "
        f"only in installer={listed - set(MANAGED_KEYS)}, "
        f"only in app={set(MANAGED_KEYS) - listed}"
    )


def test_the_changelog_documents_the_current_version() -> None:
    """Tagging a release with no changelog entry is easy to do and annoying to
    discover afterwards, when the release notes are already published."""
    changelog = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert f"## [{trading_agent.__version__}]" in changelog, (
        f"CHANGELOG.md has no '## [{trading_agent.__version__}]' section"
    )
