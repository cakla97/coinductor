from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import sys
import urllib.request

from .binance_client import BinanceApiError, BinanceClient
from .config import AppConfig, load_config
from .config_validator import ConfigValidator
from .env import load_env_file
from .portfolio_analyzer import PortfolioAnalyzer
from .research import ResearchLoader
from .runner import AgentRunner
from .storage import Storage
from .testnet_executor import TestnetExecutor
from .models import TestnetExecutedOrder, TestnetExecutionReport


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
    if args.command == "testnet-account":
        return _testnet_account_command(args)
    if args.command == "testnet-market-buy":
        return _testnet_market_buy_command(args, parser)
    if args.command == "testnet-market-sell":
        return _testnet_market_sell_command(args, parser)
    if args.command == "testnet-symbol":
        return _testnet_symbol_command(args)
    if args.command == "testnet-order-status":
        return _testnet_order_status_command(args, parser)
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

    testnet_account_parser = subparsers.add_parser("testnet-account", help="Check Binance Spot Testnet account access")
    testnet_account_parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")

    testnet_buy_parser = subparsers.add_parser("testnet-market-buy", help="Preview or submit a Spot Testnet market buy")
    testnet_buy_parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    testnet_buy_parser.add_argument("--symbol", required=True, help="Spot symbol, for example BTCUSDT")
    testnet_buy_parser.add_argument("--quote-amount", required=True, help="USDT quote amount to spend")
    testnet_buy_parser.add_argument("--client-order-id", default="", help="Optional custom client order id")
    testnet_buy_parser.add_argument("--confirm", default="", help="Must equal CONFIRM_TESTNET_ORDER to submit")

    testnet_sell_parser = subparsers.add_parser("testnet-market-sell", help="Preview or submit a Spot Testnet market sell")
    testnet_sell_parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    testnet_sell_parser.add_argument("--symbol", required=True, help="Spot symbol, for example BTCUSDT")
    testnet_sell_parser.add_argument("--quantity", default="", help="Base asset quantity to sell")
    testnet_sell_parser.add_argument("--from-last-buy", action="store_true", help="Use the last filled testnet BUY quantity from local SQLite history")
    testnet_sell_parser.add_argument("--client-order-id", default="", help="Optional custom client order id")
    testnet_sell_parser.add_argument("--confirm", default="", help="Must equal CONFIRM_TESTNET_ORDER to submit")

    testnet_symbol_parser = subparsers.add_parser("testnet-symbol", help="Inspect Spot Testnet symbol filters")
    testnet_symbol_parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    testnet_symbol_parser.add_argument("--symbol", required=True, help="Spot symbol, for example BTCUSDT")
    testnet_symbol_parser.add_argument("--quote-amount", default="10", help="Quote amount to validate")

    order_status_parser = subparsers.add_parser("testnet-order-status", help="Query a Spot Testnet order status")
    order_status_parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    order_status_parser.add_argument("--symbol", required=True, help="Spot symbol, for example BTCUSDT")
    order_status_parser.add_argument("--order-id", default="", help="Binance orderId")
    order_status_parser.add_argument("--client-order-id", default="", help="Client order id")
    return parser


def _add_common_run_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default="config.example.toml", help="Path to TOML config")
    parser.add_argument("--real-data", action="store_true", help="Use real Binance read-only data instead of mock data")
    parser.add_argument("--mock-data", action="store_true", help="Force mock data even if config disables it")
    parser.add_argument("--ai-commentary", action="store_true", help="Enable optional local LLM commentary for this run")
    parser.add_argument("--no-ai-commentary", action="store_true", help="Disable optional local LLM commentary for this run")
    parser.add_argument("--testnet-execution", action="store_true", help="Enable Spot Testnet execution for approved spot proposals")
    parser.add_argument("--no-testnet-execution", action="store_true", help="Disable Spot Testnet execution for this run")
    parser.add_argument("--confirm-testnet-order", default="", help="Must equal CONFIRM_TESTNET_ORDER to submit a Spot Testnet order")


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
    if getattr(args, "testnet_execution", False) and getattr(args, "no_testnet_execution", False):
        parser.error("--testnet-execution and --no-testnet-execution cannot be used together")
    config.raw.setdefault("testnet_execution", {})
    if getattr(args, "testnet_execution", False):
        config.raw["testnet_execution"]["enabled"] = True
    if getattr(args, "no_testnet_execution", False):
        config.raw["testnet_execution"]["enabled"] = False
    config.raw.setdefault("_runtime", {})
    config.raw["_runtime"]["testnet_confirm"] = getattr(args, "confirm_testnet_order", "")
    return config


def _run_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    config = _load_and_apply_config(args, parser)
    validation = ConfigValidator().validate(config.raw)
    _print_validation(validation)
    if validation.has_errors:
        print("Config validation failed. Fix errors before running.")
        return 2
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
    validation = ConfigValidator().validate(config.raw)
    checks.append(("Config validation", not validation.has_errors, _validation_summary(validation)))
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
    _print_validation(validation)
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
    validation = ConfigValidator().validate(config.raw)
    _print_validation(validation)
    if validation.has_errors:
        print("Config validation failed. Fix errors before generating research request.")
        return 2
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


def _testnet_account_command(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    try:
        account = BinanceClient(config.raw, use_testnet=True).testnet_account_ping()
    except BinanceApiError as exc:
        print(f"[FAIL] Binance Spot Testnet account: {exc}")
        return 1
    balances = account.get("balances", [])
    non_zero = sorted(
        row["asset"]
        for row in balances
        if Decimal(row.get("free", "0")) != 0 or Decimal(row.get("locked", "0")) != 0
    )
    watched = ["USDT", "BTC", "ETH", "BNB", "SOL", "WLD"]
    watched_available = [asset for asset in watched if asset in non_zero]
    print("[OK] Binance Spot Testnet account reachable")
    print(f"Non-zero testnet assets: {len(non_zero)}")
    print(f"Watched assets available: {_console_safe(', '.join(watched_available) if watched_available else 'none')}")
    return 0


def _testnet_market_buy_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    config = load_config(args.config)
    symbol = str(args.symbol).upper()
    quote_amount = Decimal(str(args.quote_amount))
    if quote_amount <= 0:
        parser.error("--quote-amount must be greater than zero")
    client_order_id = args.client_order_id or _default_testnet_client_order_id(symbol)
    executor = TestnetExecutor(config.raw)
    rules = executor.client.get_symbol_rules(symbol)
    validation = executor.validate_market_buy(symbol, quote_amount, rules)
    request = executor.market_buy_quote(symbol, validation.adjusted_quote_amount_usdt, client_order_id)
    print("Spot Testnet order request:")
    print(f"  symbol: {request.symbol}")
    print(f"  side: {request.side}")
    print(f"  type: {request.order_type}")
    print(f"  quoteOrderQty: {request.quote_order_qty}")
    print(f"  newClientOrderId: {request.client_order_id}")
    print(f"  validation: {validation.reason}")
    if not validation.approved:
        print("Not submitted. Local symbol filter validation rejected this order.")
        return 1
    if args.confirm != "CONFIRM_TESTNET_ORDER":
        print("Not submitted. Add --confirm CONFIRM_TESTNET_ORDER to place this on Binance Spot Testnet.")
        return 0
    result = executor.submit(request, args.confirm)
    print(f"Submitted: {result.submitted}")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    if result.response:
        print(f"Response: {result.response}")
    return 0 if result.status not in {"ERROR"} else 1


def _testnet_market_sell_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    config = load_config(args.config)
    symbol = str(args.symbol).upper()
    if args.from_last_buy:
        latest_buy = Storage(config.database_path).get_latest_filled_testnet_buy(symbol)
        if latest_buy is None:
            print(f"No filled local Spot Testnet BUY found for {symbol}.")
            return 1
        quantity = Decimal(latest_buy["executed_quantity"])
        intent_id = f"sell-{latest_buy['intent_id']}"
        source = f"last filled testnet BUY order {latest_buy['order_id']}"
    else:
        if not args.quantity:
            parser.error("--quantity is required unless --from-last-buy is used")
        quantity = Decimal(str(args.quantity))
        intent_id = f"manual-sell-{symbol.lower()}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        source = "CLI quantity"
    if quantity <= 0:
        parser.error("--quantity must be greater than zero")

    client_order_id = args.client_order_id or _default_testnet_client_order_id(f"{symbol}-sell")
    executor = TestnetExecutor(config.raw)
    rules = executor.client.get_symbol_rules(symbol)
    validation = executor.validate_market_sell(symbol, quantity, rules)
    request = executor.market_sell_quantity(symbol, validation.adjusted_quote_amount_usdt, client_order_id)
    print("Spot Testnet sell request:")
    print(f"  source: {source}")
    print(f"  symbol: {request.symbol}")
    print(f"  side: {request.side}")
    print(f"  type: {request.order_type}")
    print(f"  quantity: {request.quantity}")
    print(f"  newClientOrderId: {request.client_order_id}")
    print(f"  validation: {validation.reason}")
    if not validation.approved:
        print("Not submitted. Local symbol filter/balance validation rejected this order.")
        return 1
    if args.confirm != "CONFIRM_TESTNET_ORDER":
        print("Not submitted. Add --confirm CONFIRM_TESTNET_ORDER to place this on Binance Spot Testnet.")
        return 0
    result = executor.submit(request, args.confirm)
    print(f"Submitted: {result.submitted}")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    if result.response:
        print(f"Response: {result.response}")
    if result.submitted and result.status != "ERROR":
        _save_manual_testnet_order(config, intent_id, request, result, validation.reason)
    return 0 if result.status not in {"ERROR"} else 1


def _save_manual_testnet_order(config: AppConfig, intent_id: str, request, result, validation_summary: str) -> None:
    response = json.loads(result.response) if result.response else {}
    order_id = str(response.get("orderId", ""))
    queried_status = ""
    if order_id:
        try:
            queried = BinanceClient(config.raw, use_testnet=True).query_order(request.symbol, order_id=order_id)
            queried_status = str(queried.get("status", ""))
        except BinanceApiError as exc:
            queried_status = f"QUERY_ERROR: {exc}"
    order = TestnetExecutedOrder(
        intent_id=intent_id,
        symbol=request.symbol,
        side=request.side,
        quote_amount_usdt=Decimal(str(response.get("cummulativeQuoteQty", "0"))),
        client_order_id=request.client_order_id,
        submitted=result.submitted,
        status=result.status,
        executed_quantity=Decimal(str(response.get("executedQty", "0"))),
        cumulative_quote_qty=Decimal(str(response.get("cummulativeQuoteQty", "0"))),
        order_id=order_id,
        queried_status=queried_status,
        validation_summary=validation_summary,
        message=result.message,
    )
    storage = Storage(config.database_path)
    run_id = storage.start_run("TESTNET_MANUAL")
    storage.save_testnet_execution(run_id, TestnetExecutionReport(enabled=True, orders=(order,), summary="Manual Spot Testnet CLI order."))
    storage.finish_run(run_id, "OK", f"Manual Spot Testnet {request.side} order {order_id} saved.")


def _testnet_symbol_command(args: argparse.Namespace) -> int:
    config = load_config(args.config)
    executor = TestnetExecutor(config.raw)
    rules = executor.client.get_symbol_rules(str(args.symbol).upper())
    validation = executor.validate_market_buy(rules.symbol, Decimal(str(args.quote_amount)), rules)
    print(f"Symbol: {rules.symbol}")
    print(f"Status: {rules.status}")
    print(f"Base/quote: {rules.base_asset}/{rules.quote_asset}")
    print(f"quoteOrderQtyMarketAllowed: {rules.quote_order_qty_market_allowed}")
    print(f"minNotional: {rules.min_notional}")
    print(f"minQty: {rules.min_qty}")
    print(f"stepSize: {rules.step_size}")
    print(f"tickSize: {rules.tick_size}")
    print(f"Validation approved: {validation.approved}")
    print(f"Validation reason: {validation.reason}")
    print(f"Adjusted quote amount: {validation.adjusted_quote_amount_usdt}")
    return 0 if validation.approved else 1


def _testnet_order_status_command(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if not args.order_id and not args.client_order_id:
        parser.error("--order-id or --client-order-id is required")
    config = load_config(args.config)
    try:
        order = BinanceClient(config.raw, use_testnet=True).query_order(
            symbol=str(args.symbol).upper(),
            order_id=args.order_id or None,
            client_order_id=args.client_order_id or None,
        )
    except BinanceApiError as exc:
        print(f"[FAIL] Spot Testnet order query: {exc}")
        return 1
    print(f"Symbol: {order.get('symbol', '')}")
    print(f"Order ID: {order.get('orderId', '')}")
    print(f"Client order ID: {order.get('clientOrderId', '')}")
    print(f"Side/type: {order.get('side', '')}/{order.get('type', '')}")
    print(f"Status: {order.get('status', '')}")
    print(f"Executed quantity: {order.get('executedQty', '')}")
    print(f"Cumulative quote: {order.get('cummulativeQuoteQty', '')}")
    return 0


def _default_testnet_client_order_id(symbol: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"bta-{symbol.lower()}-{timestamp}"


def _console_safe(value: str) -> str:
    return value.encode("ascii", errors="backslashreplace").decode("ascii")


def _validation_summary(validation) -> str:
    errors = sum(1 for issue in validation.issues if issue.severity == "ERROR")
    warnings = sum(1 for issue in validation.issues if issue.severity == "WARNING")
    return f"{errors} error(s), {warnings} warning(s)"


def _print_validation(validation) -> None:
    for issue in validation.issues:
        print(f"[{issue.severity}] {issue.path}: {issue.message}")
