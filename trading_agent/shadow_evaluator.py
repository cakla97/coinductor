from __future__ import annotations

from decimal import Decimal
import json

from .binance_client import BinanceClient
from .models import MarketSnapshot, ShadowEvaluation, ShadowEvaluationReport, ShadowSignal, TradeProposal
from .storage import Storage


class ShadowEvaluator:
    def __init__(self, config: dict, storage: Storage, client: BinanceClient | None = None):
        self.config = config
        self.storage = storage
        self.client = client

    def process(
        self,
        run_id: int,
        proposal: TradeProposal,
        snapshots: list[MarketSnapshot],
    ) -> ShadowEvaluationReport:
        shadow = self.config.get("shadow_evaluation", {})
        if not shadow.get("enabled", True):
            return ShadowEvaluationReport(
                False,
                None,
                "DISABLED",
                "Shadow evaluation is disabled.",
                (),
                0,
                0,
                0,
                0,
                0,
                "Shadow evaluation is disabled.",
            )

        newly_evaluated = self._evaluate_due(run_id, snapshots)
        current_signal, recording_status, recording_message = self._record_current(run_id, proposal, snapshots)
        counts = self.storage.get_shadow_evaluation_counts()
        summary = (
            f"{counts['pending']} pending, {counts['completed']} completed shadow signal(s): "
            f"{counts['correct']} correct, {counts['wrong']} wrong, {counts['neutral']} neutral."
        )
        return ShadowEvaluationReport(
            enabled=True,
            current_signal=current_signal,
            recording_status=recording_status,
            recording_message=recording_message,
            newly_evaluated=tuple(newly_evaluated),
            pending_count=counts["pending"],
            completed_count=counts["completed"],
            correct_count=counts["correct"],
            wrong_count=counts["wrong"],
            neutral_count=counts["neutral"],
            summary=summary,
        )

    def _record_current(
        self,
        run_id: int,
        proposal: TradeProposal,
        snapshots: list[MarketSnapshot],
    ) -> tuple[ShadowSignal | None, str, str]:
        shadow = self.config.get("shadow_evaluation", {})
        if shadow.get("require_ai_enabled", True) and not self.config.get("ai", {}).get("enabled", False):
            return None, "SKIPPED_AI_DISABLED", "AI proposals are disabled, so no shadow signal was recorded."
        min_interval = int(shadow.get("min_signal_interval_hours", 20))
        cooldown = self.storage.get_shadow_signal_cooldown(run_id, min_interval)
        if cooldown is not None:
            message = (
                f"Shadow signal skipped: run {cooldown['run_id']} already recorded "
                f"{cooldown['action']} {cooldown['symbol']} {cooldown['elapsed_hours']:.2f} hours ago. "
                f"Approximately {cooldown['remaining_hours']:.2f} hours remain in the {min_interval}-hour cooldown."
            )
            return None, "SKIPPED_COOLDOWN", message
        price_by_symbol = {snapshot.symbol.upper(): snapshot.price for snapshot in snapshots}
        entry_price = price_by_symbol.get(proposal.symbol.upper())
        if entry_price is None or entry_price <= 0:
            return None, "SKIPPED_NO_PRICE", f"No positive market price is available for {proposal.symbol}."
        horizon_hours = int(shadow.get("horizon_hours", 24))
        universe_prices = {symbol: str(price) for symbol, price in price_by_symbol.items() if price > 0}
        inserted = self.storage.save_shadow_signal(
            run_id=run_id,
            proposal=proposal,
            entry_price=entry_price,
            horizon_hours=horizon_hours,
            universe_entry_prices=json.dumps(universe_prices, sort_keys=True),
        )
        if not inserted:
            return None, "SKIPPED_DUPLICATE_RUN", f"Run {run_id} already has a shadow signal."
        signal = ShadowSignal(
            run_id=run_id,
            symbol=proposal.symbol,
            action=proposal.action,
            confidence=proposal.confidence,
            entry_price=entry_price,
            horizon_hours=horizon_hours,
            status="PENDING",
        )
        return signal, "RECORDED", f"Recorded shadow signal {proposal.action} {proposal.symbol} for run {run_id}."

    def _evaluate_due(self, run_id: int, snapshots: list[MarketSnapshot]) -> list[ShadowEvaluation]:
        price_by_symbol = {snapshot.symbol.upper(): snapshot.price for snapshot in snapshots}
        threshold = Decimal(str(self.config.get("shadow_evaluation", {}).get("decision_threshold_pct", "0.5")))
        evaluations: list[ShadowEvaluation] = []
        for row in self.storage.get_due_shadow_signals(run_id):
            symbol = str(row["symbol"]).upper()
            universe_entries = json.loads(str(row["universe_entry_prices"] or "{}"))
            evaluation_prices, price_source = self._evaluation_prices(
                tuple(universe_entries),
                int(row["target_timestamp_ms"]),
                price_by_symbol,
            )
            evaluation_price = evaluation_prices.get(symbol)
            if evaluation_price is None or evaluation_price <= 0:
                continue
            entry_price = Decimal(str(row["entry_price"]))
            symbol_return = self._return_pct(entry_price, evaluation_price)
            universe_returns = {
                candidate: self._return_pct(Decimal(str(entry)), evaluation_prices[candidate])
                for candidate, entry in universe_entries.items()
                if candidate in evaluation_prices and Decimal(str(entry)) > 0
            }
            if universe_returns:
                best_symbol, best_return = max(universe_returns.items(), key=lambda item: item[1])
            else:
                best_symbol, best_return = symbol, symbol_return
            verdict, score = self._verdict(str(row["action"]), symbol_return, best_return, threshold)
            elapsed_hours = Decimal(str(row["evaluation_delay_hours"]))
            evaluation = ShadowEvaluation(
                signal_run_id=int(row["run_id"]),
                evaluated_run_id=run_id,
                symbol=symbol,
                action=str(row["action"]),
                entry_price=entry_price,
                evaluation_price=evaluation_price,
                elapsed_hours=elapsed_hours,
                symbol_return_pct=symbol_return,
                best_universe_symbol=best_symbol,
                best_universe_return_pct=best_return,
                verdict=verdict,
                score=score,
                price_source=price_source,
            )
            self.storage.complete_shadow_signal(evaluation)
            evaluations.append(evaluation)
        return evaluations

    def _evaluation_prices(
        self,
        symbols: tuple[str, ...],
        target_timestamp_ms: int,
        fallback_prices: dict[str, Decimal],
    ) -> tuple[dict[str, Decimal], str]:
        prices: dict[str, Decimal] = {}
        historical_count = 0
        for symbol in symbols:
            if self.client is not None:
                try:
                    prices[symbol] = self.client.get_historical_close(symbol, target_timestamp_ms)
                    historical_count += 1
                    continue
                except Exception:
                    pass
            fallback = fallback_prices.get(symbol)
            if fallback is not None:
                prices[symbol] = fallback
        if prices and historical_count == len(prices) == len(symbols):
            return prices, "BINANCE_1M_AT_HORIZON"
        if historical_count > 0:
            return prices, "MIXED_HISTORICAL_CURRENT_FALLBACK"
        return prices, "CURRENT_SNAPSHOT_FALLBACK"

    def _verdict(
        self,
        action: str,
        symbol_return: Decimal,
        best_universe_return: Decimal,
        threshold: Decimal,
    ) -> tuple[str, str]:
        if action == "BUY":
            if symbol_return >= threshold:
                return "BUY_GAIN", "CORRECT"
            if symbol_return <= -threshold:
                return "BUY_LOSS", "WRONG"
            return "BUY_FLAT", "NEUTRAL"
        if action == "HOLD":
            if best_universe_return >= threshold:
                return "HOLD_MISSED_GAIN", "WRONG"
            if best_universe_return <= -threshold:
                return "HOLD_AVOIDED_LOSS", "CORRECT"
            return "HOLD_NEUTRAL", "NEUTRAL"
        return "UNSUPPORTED_ACTION", "NEUTRAL"

    def _return_pct(self, entry_price: Decimal, evaluation_price: Decimal) -> Decimal:
        if entry_price == 0:
            return Decimal("0")
        return (evaluation_price / entry_price - Decimal("1")) * Decimal("100")
