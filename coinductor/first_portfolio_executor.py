from __future__ import annotations

from dataclasses import replace
from decimal import Decimal, ROUND_HALF_UP

from trading_agent.binance_client import BinanceApiError
from trading_agent.config import default_config_path, load_config
from trading_agent.live_preview import LivePreviewExecutor
from trading_agent.models import FirstPortfolioTrancheResult, TradeProposal
from trading_agent.order_journal import OrderIntentFactory
from trading_agent.risk_engine import RiskEngine
from trading_agent.runtime_flags import RuntimeFlags
from trading_agent.storage import Storage
from trading_agent.testnet_executor import TestnetExecutor

from .secret_store import load_secrets

TESTNET_QUOTE_ASSET = "USDT"


class FirstPortfolioExecutor:
    """Desktop-side orchestrator for guarded, staged first-portfolio deployment.

    This intentionally does not go through AgentRunner.run() (a single full
    analytical pass); it reuses the same deterministic, guarded primitives
    (RiskEngine, LivePreviewExecutor, TestnetExecutor, Storage) directly, one
    basket asset/tranche at a time, the same way connection_check.py talks to
    BinanceClient directly for a narrower purpose.
    """

    def __init__(self, config_path: str | None = None, env_path: str = ".env"):
        self.config_path = config_path or default_config_path()
        self.env_path = env_path

    def run_tranche(
        self,
        asset: str,
        target_pct: Decimal,
        total_budget: Decimal,
        tranche_index: int,
        tranches_total: int,
        mode: str,
        submit: bool = False,
        confirm: str = "",
    ) -> FirstPortfolioTrancheResult:
        mode = mode.strip().upper()
        if mode not in {"TESTNET", "MAINNET"}:
            raise ValueError("mode must be TESTNET or MAINNET.")
        if tranches_total <= 0 or not (1 <= tranche_index <= tranches_total):
            raise ValueError("tranche_index must be between 1 and tranches_total.")

        load_secrets(self.env_path)
        config = load_config(self.config_path)
        quote_asset = TESTNET_QUOTE_ASSET if mode == "TESTNET" else str(
            config.raw.get("live_confirm", {}).get("quote_asset", "USDC")
        ).upper()
        symbol = f"{asset.upper()}{quote_asset}"
        quote_amount = self._tranche_amount(target_pct, total_budget, tranches_total)

        storage = Storage(config.database_path)
        intent_id = OrderIntentFactory(config.raw).first_portfolio_intent_id(asset.upper(), mode, tranche_index)
        existing_intents = storage.get_existing_first_portfolio_intents(mode)
        run_id = storage.start_run("FIRST_PORTFOLIO")
        try:
            if intent_id in existing_intents:
                result = FirstPortfolioTrancheResult(
                    intent_id=intent_id,
                    mode=mode,
                    asset=asset.upper(),
                    symbol=symbol,
                    tranche_index=tranche_index,
                    tranches_total=tranches_total,
                    quote_amount=quote_amount,
                    status="ALREADY_DONE",
                    validation_summary=f"Tranche {tranche_index}/{tranches_total} for {asset.upper()} was already completed on {mode.lower()}.",
                    confirmation_required="CONFIRM_MAINNET_ORDER" if mode == "MAINNET" else "CONFIRM_TESTNET_ORDER",
                    submitted=True,
                )
                storage.finish_run(run_id, "OK", result.validation_summary)
                return result

            proposal = TradeProposal(
                symbol=symbol,
                action="BUY",
                confidence=Decimal("1"),
                quote_amount_usdt=quote_amount,
                stop_loss_pct=Decimal(str(config.raw["orders"]["default_stop_loss_pct"])),
                take_profit_pct=Decimal(str(config.raw["orders"]["default_take_profit_pct"])),
                reason=f"First portfolio deployment: tranche {tranche_index}/{tranches_total} for {asset.upper()}.",
            )
            risk_state = storage.get_live_risk_state(run_id, config.raw)
            risk_decision = RiskEngine(config.raw).evaluate(
                proposal=proposal,
                risk_state=risk_state,
                snapshots=[],
                skip_consensus=True,
                allowed_symbols={symbol},
            )
            if not risk_decision.approved:
                result = FirstPortfolioTrancheResult(
                    intent_id=intent_id,
                    mode=mode,
                    asset=asset.upper(),
                    symbol=symbol,
                    tranche_index=tranche_index,
                    tranches_total=tranches_total,
                    quote_amount=quote_amount,
                    status="BLOCKED",
                    validation_summary=risk_decision.reason,
                    confirmation_required="CONFIRM_MAINNET_ORDER" if mode == "MAINNET" else "CONFIRM_TESTNET_ORDER",
                )
                storage.save_first_portfolio_tranche(run_id, result)
                storage.finish_run(run_id, "OK", result.validation_summary)
                return result

            if mode == "TESTNET":
                result = self._run_testnet(config.raw, proposal, risk_decision, intent_id, asset.upper(), existing_intents, tranche_index, tranches_total, submit, confirm)
            else:
                result = self._run_mainnet(config.raw, proposal, risk_decision, intent_id, asset.upper(), existing_intents, tranche_index, tranches_total, submit, confirm)

            storage.save_first_portfolio_tranche(run_id, result)
            storage.finish_run(run_id, "OK", result.validation_summary)
            return result
        except Exception as exc:
            storage.finish_run(run_id, "ERROR", str(exc))
            raise

    def _run_testnet(
        self,
        config: dict,
        proposal: TradeProposal,
        risk_decision,
        intent_id: str,
        asset: str,
        existing_intents: set[str],
        tranche_index: int,
        tranches_total: int,
        submit: bool,
        confirm: str,
    ) -> FirstPortfolioTrancheResult:
        # Deliberately bypasses TestnetExecutor.execute_spot_proposal(): that method
        # gates on testnet_execution.enabled (a separate, unrelated feature toggle)
        # and enforces strategy.allowed_symbols, which is expressed in mainnet quote
        # terms (e.g. BTCUSDC) and would incorrectly reject every Testnet symbol
        # (BTCUSDT). This calls the same underlying validate/submit primitives
        # directly with require_whitelist=False instead.
        executor = TestnetExecutor(config)
        try:
            rules = executor.client.get_symbol_rules(proposal.symbol)
        except BinanceApiError as exc:
            return FirstPortfolioTrancheResult(
                intent_id=intent_id,
                mode="TESTNET",
                asset=asset,
                symbol=proposal.symbol,
                tranche_index=tranche_index,
                tranches_total=tranches_total,
                quote_amount=proposal.quote_amount_usdt,
                status="BLOCKED",
                validation_summary=str(exc),
                confirmation_required="CONFIRM_TESTNET_ORDER",
            )
        validation = executor.validate_market_buy(
            proposal.symbol, risk_decision.adjusted_quote_amount_usdt, rules, require_whitelist=False
        )
        if not validation.approved:
            return FirstPortfolioTrancheResult(
                intent_id=intent_id,
                mode="TESTNET",
                asset=asset,
                symbol=proposal.symbol,
                tranche_index=tranche_index,
                tranches_total=tranches_total,
                quote_amount=proposal.quote_amount_usdt,
                status="BLOCKED",
                validation_summary=validation.reason,
                confirmation_required="CONFIRM_TESTNET_ORDER",
            )
        request = executor.market_buy_quote(
            symbol=proposal.symbol,
            quote_amount_usdt=validation.adjusted_quote_amount_usdt,
            client_order_id=f"bta-fp-{intent_id}",
        )
        if not submit:
            # Do not ask submit() what it thinks of an empty confirmation. It
            # answers "Confirmation string did not match CONFIRM_TESTNET_ORDER",
            # which is true and completely misleading here: nobody asked it to
            # submit. Validate-only reported itself as a failed confirmation,
            # and read as if the tranche could never be sent.
            return FirstPortfolioTrancheResult(
                intent_id=intent_id,
                mode="TESTNET",
                asset=asset,
                symbol=proposal.symbol,
                tranche_index=tranche_index,
                tranches_total=tranches_total,
                quote_amount=proposal.quote_amount_usdt,
                status="VALIDATED",
                validation_summary=validation.reason,
                confirmation_required="CONFIRM_TESTNET_ORDER",
                submitted=False,
            )
        result = executor.submit(request, confirm)
        order = executor._executed_order_from_result(intent_id, request, result, validation.reason)
        return FirstPortfolioTrancheResult(
            intent_id=intent_id,
            mode="TESTNET",
            asset=asset,
            symbol=proposal.symbol,
            tranche_index=tranche_index,
            tranches_total=tranches_total,
            quote_amount=proposal.quote_amount_usdt,
            status=order.status,
            validation_summary=order.validation_summary,
            confirmation_required="CONFIRM_TESTNET_ORDER",
            submitted=order.submitted,
            order_id=order.order_id,
            executed_quantity=order.executed_quantity,
            cumulative_quote_qty=order.cumulative_quote_qty,
            message=order.message,
        )

    def _run_mainnet(
        self,
        config: dict,
        proposal: TradeProposal,
        risk_decision,
        intent_id: str,
        asset: str,
        existing_intents: set[str],
        tranche_index: int,
        tranches_total: int,
        submit: bool,
        confirm: str,
    ) -> FirstPortfolioTrancheResult:
        # replace() rather than a fresh RuntimeFlags: this narrows authority to the
        # live buy for this tranche without disturbing any other flag already set.
        replace(
            RuntimeFlags.from_config(config),
            live_submit=bool(submit),
            mainnet_confirm=confirm if submit else "",
        ).store_in(config)
        config.setdefault("live_confirm", {})
        config["live_confirm"]["enabled"] = True
        report = LivePreviewExecutor(config).preview_spot_proposal(
            proposal=proposal,
            risk_decision=risk_decision,
            bankroll=None,
            existing_intents=existing_intents,
            require_whitelist=False,
        )
        order = report.orders[0] if report.orders else None
        if order is None:
            return FirstPortfolioTrancheResult(
                intent_id=intent_id,
                mode="MAINNET",
                asset=asset,
                symbol=proposal.symbol,
                tranche_index=tranche_index,
                tranches_total=tranches_total,
                quote_amount=proposal.quote_amount_usdt,
                status="BLOCKED",
                validation_summary=report.summary,
                confirmation_required="CONFIRM_MAINNET_ORDER",
            )
        return FirstPortfolioTrancheResult(
            intent_id=intent_id,
            mode="MAINNET",
            asset=asset,
            symbol=proposal.symbol,
            tranche_index=tranche_index,
            tranches_total=tranches_total,
            quote_amount=proposal.quote_amount_usdt,
            status=order.status,
            validation_summary=order.validation_summary,
            confirmation_required=order.confirmation_required,
            submitted=order.submitted,
            order_id=order.order_id,
            executed_quantity=order.executed_quantity,
            cumulative_quote_qty=order.cumulative_quote_qty,
            message=order.message,
        )

    def _tranche_amount(self, target_pct: Decimal, total_budget: Decimal, tranches_total: int) -> Decimal:
        per_asset = total_budget * target_pct / Decimal("100")
        per_tranche = per_asset / Decimal(tranches_total)
        return per_tranche.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
