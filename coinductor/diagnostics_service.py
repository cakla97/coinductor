from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path
import platform
import sqlite3
import sys

from trading_agent.config import default_config_path, load_config

from . import __version__
from .safety_service import SafetyService
from .setup_service import SetupService


class DiagnosticsService:
    """Builds a sanitized, shareable diagnostics report.

    The report intentionally contains no secrets: API keys and .env values
    are never read into it (credential state is reported as present/absent
    only), and personal portfolio holdings, balances, and amounts are left
    out. It is safe to attach to a support request or GitHub issue.
    """

    def __init__(
        self,
        config_path: str | Path | None = None,
        env_path: str | Path = ".env",
        safety_path: str | Path = "state/app_safety_state.toml",
    ):
        self.config_path = Path(config_path or default_config_path())
        self.env_path = Path(env_path)
        self.safety_path = Path(safety_path)

    def generate_report(self) -> str:
        lines: list[str] = []
        lines.append("Coinductor diagnostics bundle")
        lines.append("This report contains no API keys, secrets, balances, or holdings.")
        lines.append(f"Generated: {datetime.now(UTC).isoformat(timespec='seconds')}")
        lines.append("")
        self._system_section(lines)
        self._setup_section(lines)
        self._safety_section(lines)
        self._config_section(lines)
        self._runs_section(lines)
        return "\n".join(lines) + "\n"

    def write_bundle(self, directory: str | Path = "outputs/diagnostics") -> Path:
        target_dir = Path(directory)
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        path = target_dir / f"coinductor-diagnostics-{stamp}.txt"
        path.write_text(self.generate_report(), encoding="utf-8")
        return path

    def _system_section(self, lines: list[str]) -> None:
        lines.append("[System]")
        lines.append(f"App version: {__version__}")
        lines.append(f"Python: {sys.version.split()[0]}")
        lines.append(f"Platform: {platform.platform()}")
        lines.append(f"Frozen build: {'yes' if getattr(sys, 'frozen', False) else 'no'}")
        lines.append(f"PySide6: {self._pyside_version()}")
        lines.append(f"Working directory: {Path.cwd()}")
        lines.append("")

    def _setup_section(self, lines: list[str]) -> None:
        lines.append("[Setup checks]")
        try:
            snapshot = SetupService(self.config_path, self.env_path).inspect()
            for check in snapshot.checks:
                lines.append(f"  [{check['status']}] {check['name']}: {check['detail']}")
        except Exception as exc:  # never let one section break the bundle
            lines.append(f"  (unavailable: {type(exc).__name__})")
        lines.append("")

    def _safety_section(self, lines: list[str]) -> None:
        lines.append("[Safety stage]")
        try:
            snapshot = SafetyService(self.safety_path).inspect()
            lines.append(f"  Stage: {snapshot.stage}")
            lines.append(f"  Live preview allowed: {snapshot.allows_live_preview}")
            lines.append(f"  Live submit allowed: {snapshot.allows_live_submit}")
        except Exception as exc:
            lines.append(f"  (unavailable: {type(exc).__name__})")
        lines.append("")

    def _config_section(self, lines: list[str]) -> None:
        lines.append("[Config summary]")
        lines.append(f"  Config file: {self.config_path.name}")
        try:
            if not self.config_path.exists():
                lines.append("  (config file missing)")
                lines.append("")
                return
            raw = load_config(self.config_path).raw
            app = raw.get("app", {})
            lines.append(f"  Mode: {app.get('mode', 'unknown')}")
            lines.append(f"  Mock data: {app.get('mock_data', 'unknown')}")
            for section in ("ai", "research", "grid_bot", "rebalancing", "testnet_execution", "live_confirm"):
                enabled = raw.get(section, {}).get("enabled", "n/a")
                lines.append(f"  {section}.enabled: {enabled}")
        except Exception as exc:
            lines.append(f"  (unavailable: {type(exc).__name__})")
        lines.append("")

    def _runs_section(self, lines: list[str]) -> None:
        lines.append("[Run history]")
        try:
            database_path = load_config(self.config_path).database_path if self.config_path.exists() else None
            if database_path is None or not Path(database_path).exists():
                lines.append("  (no run database yet)")
                lines.append("")
                return
            connection = sqlite3.connect(Path(database_path))
            try:
                total = connection.execute("select count(*) from runs").fetchone()[0]
                lines.append(f"  Total runs: {total}")
                rows = connection.execute(
                    "select started_at, mode, status from runs order by id desc limit 5"
                ).fetchall()
                for started_at, mode, status in rows:
                    lines.append(f"  {started_at} | {mode} | {status}")
            finally:
                connection.close()
        except Exception as exc:
            lines.append(f"  (unavailable: {type(exc).__name__})")
        lines.append("")

    def _pyside_version(self) -> str:
        try:
            import PySide6  # noqa: PLC0415

            return str(PySide6.__version__)
        except Exception:
            return "not available"
