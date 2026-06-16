from __future__ import annotations

import argparse

from .config import load_config
from .runner import AgentRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Periodic Binance trading agent MVP")
    parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    runner = AgentRunner(config)
    result = runner.run()
    print(f"Run {result.run_id} finished: {result.status}")
    print(f"Report: {result.report_path}")
    return 0 if result.status == "OK" else 1

