from __future__ import annotations

import argparse

from .config import load_config
from .env import load_env_file
from .runner import AgentRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Periodic Binance trading agent MVP")
    parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    parser.add_argument("--real-data", action="store_true", help="Use real Binance read-only data instead of mock data")
    parser.add_argument("--mock-data", action="store_true", help="Force mock data even if config disables it")
    args = parser.parse_args(argv)

    load_env_file()
    config = load_config(args.config)
    if args.real_data and args.mock_data:
        parser.error("--real-data and --mock-data cannot be used together")
    if args.real_data:
        config.raw["app"]["mock_data"] = False
    if args.mock_data:
        config.raw["app"]["mock_data"] = True
    runner = AgentRunner(config)
    result = runner.run()
    print(f"Run {result.run_id} finished: {result.status}")
    print(f"Report: {result.report_path}")
    return 0 if result.status == "OK" else 1
