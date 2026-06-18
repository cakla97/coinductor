from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.request

from .binance_client import BinanceApiError, BinanceClient
from .config import AppConfig, load_config
from .env import load_env_file
from .portfolio_analyzer import PortfolioAnalyzer
from .research import ResearchLoader
from .runner import AgentRunner


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    if not argv or argv[0].startswith("-"):
        return _run_legacy(argv)

    parser = _build_parser()
    args = parser.parse_args(argv)
    load_env_file()

    if args.command == "run":
        return _run_command(args, parser)
    if args.command == "doctor":
        return _doctor_command(args)
    if args.command == "last-report":
        return _last_report_command(args)
    if args.command == "research-request":
        return _research_request_command(args)
    parser.error(f"Unknown command {args.command}")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Periodic Binance portfolio assistant")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the portfolio assistant")
    _add_common_run_args(run_parser)

    doctor_parser = subparsers.add_parser("doctor", help="Check local setup and optional integrations")
    doctor_parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    doctor_parser.add_argument("--real-data", action="store_true", help="Check Binance API read-only permissions")
    doctor_parser.add_argument("--ai-commentary", action="store_true", help="Check local OpenAI-compatible LLM endpoint")

    last_parser = subparsers.add_parser("last-report", help="Print the latest report path")
    last_parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")

    request_parser = subparsers.add_parser("research-request", help="Generate a Binance skills research request")
    request_parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    request_parser.add_argument("--real-data", action="store_true", help="Use real Binance read-only data for portfolio context")
    request_parser.add_argument("--mock-data", action="store_true", help="Use mock data for portfolio context")
    return parser


def _add_common_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    parser.add_argument("--real-data", action="store_true", help="Use real Binance read-only data instead of mock data")
    parser.add_argument("--mock-data", action="store_true", help="Force mock data even if config disables it")
    parser.add_argument("--ai-commentary", action="store_true", help="Enable optional local LLM commentary for this run")
    parser.add_argument("--no-ai-commentary", action="store_true", help="Disable optional local LLM commentary for this run")


def _run_legacy(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Periodic Binance portfolio assistant")
    _add_common_run_args(parser)
    args = parser.parse_args(argv)
    load_env_file()
    return _run_command(args, parser)


def _load_and_apply_config(args: argparse.Namespace, parser: argparse.ArgumentParser) -> AppConfig:
    config = load_config(args.config)
    if getattr(args, "real_data", False) and getattr(args, "mock_data", False):
        parser.error("--real-data and --mock-data cannot be used together")
    if getattr(args, "real_data", False):
        config.raw["app"]["mock_data"] = False
    if getattr(args, "mock_data", False):
        config.raw["app"]["mock_data"] = True
    if getattr(args, "ai_commentary", False) and getattr(args, "no_ai_commentary", False):
        parser.error("--ai-commentary and --no-ai-commentary cannot be used together")
    if getattr(args, "ai_commentary", False):
        config.raw["ai"]["commentary_enabled"] = True
    if getattr(args, "no_ai_commentary", False):
        config.raw["ai"]["commentary_enabled"] = False
    return config


def _run_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    config = _load_and_apply_config(args, parser)
    runner = AgentRunner(config)
    result = runner.run()
    print(f"Run {result.run_id} finished: {result.status}")
    print(f"Report: {result.report_path}")
    return 0 if result.status == "OK" else 1


def _doctor_command(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    checks: list[tuple[str, bool, str]] = []
    checks.append(("Python", True, sys.version.split()[0]))
    checks.append(("Config", config.path.exists(), str(config.path)))
    checks.append((".env", Path(".env").exists(), "present" if Path(".env").exists() else "missing"))

    for path in [
        config.reports_dir,
        Path(config.raw.get("research", {}).get("notes_dir", "research/notes")),
        Path(config.raw.get("research", {}).get("requests_dir", "research/requests")),
        Path(config.raw.get("app", {}).get("active_strategies_path", "state/active_strategies.toml")).parent,
    ]:
        path.mkdir(parents=True, exist_ok=True)
        checks.append((f"Directory {path}", path.exists(), "ok" if path.exists() else "missing"))

    if args.real_data:
        try:
            client = BinanceClient(config.raw)
            client.assert_read_only_permissions()
            checks.append(("Binance read-only API", True, "permissions ok"))
        except BinanceApiError as exc:
            checks.append(("Binance read-only API", False, str(exc)))

    if args.ai_commentary:
        checks.append(_check_llm(config))

    ok = True
    for name, passed, detail in checks:
        ok = ok and passed
        status = "OK" if passed else "FAIL"
        print(f"[{status}] {name}: {detail}")
    return 0 if ok else 1


def _check_llm(config: AppConfig) -> tuple[str, bool, str]:
    ai_config = config.raw.get("ai", {})
    base_url = os.getenv(str(ai_config.get("base_url_env", "LLM_BASE_URL")), "").rstrip("/")
    if not base_url:
        return ("LLM endpoint", False, "LLM_BASE_URL is not set")
    try:
        request = urllib.request.Request(f"{base_url}/models", method="GET")
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = [item.get("id", "") for item in payload.get("data", [])]
        return ("LLM endpoint", True, ", ".join(models) if models else "reachable")
    except Exception as exc:
        return ("LLM endpoint", False, str(exc))


def _last_report_command(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    reports = sorted(config.reports_dir.glob("*_run-*.md"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not reports:
        print("No reports found.")
        return 1
    print(reports[0])
    return 0


def _research_request_command(args: argparse.Namespace) -> int:
    parser = argparse.ArgumentParser()
    config = _load_and_apply_config(args, parser)
    client = BinanceClient(config.raw)
    balances = client.get_balances()
    portfolio_assets = sorted(
        {balance.asset for balance in balances}
        | {asset.upper() for asset in config.raw.get("portfolio", {}).get("tracked_assets", [])}
    )
    asset_prices = client.get_asset_prices_usdt(portfolio_assets)
    portfolio = PortfolioAnalyzer(config.raw).analyze(balances, asset_prices)
    status = ResearchLoader(config.raw).status_and_request(portfolio)
    if status.request is None:
        print(status.summary)
        return 0
    print(status.request.path)
    return 0
