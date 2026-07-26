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
