from __future__ import annotations

from collections.abc import Callable

from trading_agent.config import load_config
from trading_agent.config_validator import ConfigValidator
from trading_agent.env import load_env_file
from trading_agent.runner import AgentRunner

from .models import DesktopRunResult, RunOptions
from .report_summary import ReportSummaryReader


ProgressCallback = Callable[[str, int], None]


class CoinductorApplication:
    def __init__(self, summary_reader: ReportSummaryReader | None = None):
        self.summary_reader = summary_reader or ReportSummaryReader()

    def run_analysis(
        self,
        options: RunOptions,
        progress: ProgressCallback | None = None,
    ) -> DesktopRunResult:
        notify = progress or (lambda _message, _percent: None)
        notify("Loading configuration", 8)
        load_env_file()
        config = load_config(options.config_path)
        self._apply_options(config.raw, options)

        notify("Validating safety policy", 18)
        validation = ConfigValidator().validate(config.raw)
        if validation.has_errors:
            messages = "; ".join(
                f"{issue.path}: {issue.message}"
                for issue in validation.issues
                if issue.severity == "ERROR"
            )
            raise ValueError(f"Configuration validation failed: {messages}")

        notify("Loading portfolio and market data", 32)
        runner = AgentRunner(config)
        notify("Running deterministic analysis", 48)
        result = runner.run()
        notify("Preparing dashboard summary", 92)
        summary = self.summary_reader.read(result.run_id, result.status, result.report_path)
        notify("Analysis complete", 100)
        return summary

    def _apply_options(self, config: dict, options: RunOptions) -> None:
        mode = options.data_mode.upper()
        if mode not in {"REAL", "MOCK"}:
            raise ValueError("data_mode must be REAL or MOCK.")
        config["app"]["mock_data"] = mode == "MOCK"
        config["ai"]["commentary_enabled"] = bool(options.ai_summary)
        config["ai"]["enabled"] = bool(options.ai_proposals)
        config["live_confirm"]["enabled"] = bool(options.live_preview or options.live_submit)
        config.setdefault("_runtime", {})
        config["_runtime"].update(
            {
                "live_submit": bool(options.live_submit),
                "mainnet_confirm": options.live_confirm if options.live_submit else "",
                "earn_redeem_submit": False,
                "earn_redeem_confirm": "",
                "oco_protection_submit": bool(options.oco_submit),
                "mainnet_oco_confirm": options.oco_confirm if options.oco_submit else "",
                "testnet_confirm": "",
            }
        )
