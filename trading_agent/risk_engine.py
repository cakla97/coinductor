from __future__ import annotations

from decimal import Decimal

from .decimal_utils import display
from .messages import Message, render_message
from .models import (
    TREND_INSUFFICIENT_HISTORY,
    LiveRiskState,
    MarketSnapshot,
    RiskDecision,
    TradeProposal,
)


class RiskEngine:
    def __init__(self, config: dict):
        self.config = config

    def evaluate(
        self,
        proposal: TradeProposal,
        risk_state: LiveRiskState,
        snapshots: list[MarketSnapshot],
        skip_consensus: bool = False,
        allowed_symbols: set[str] | None = None,
        *,
        portfolio_value: Decimal | None,
        spendable_quote: Decimal | None,
    ) -> RiskDecision:
        """Rule on a proposal, and decide how large it may actually be.

        `portfolio_value` and `spendable_quote` are keyword-only and have no
        default on purpose. They shrink the approved amount, so a caller that
        forgot them would silently get the most permissive sizing available -
        exactly the failure mode `RuntimeFlags` is built to avoid. Passing
        `None` is allowed but has to be written down at the call site, where
        the reason for it can be read.
        """
        risk = self.config["risk"]
        # allowed_symbols lets a caller substitute a different, still-enforced
        # whitelist (e.g. a first-portfolio template's basket) instead of
        # strategy.allowed_symbols, which is specifically the tactical-trading
        # universe and may not include every basket asset. The symbol still has
        # to be in *some* explicit whitelist; this never disables the check.
        if allowed_symbols is None:
            allowed_symbols = set(self.config["strategy"]["allowed_symbols"])

        if proposal.symbol not in allowed_symbols:
            return self._reject(Message("risk_not_whitelisted", {"symbol": proposal.symbol}))
        if proposal.action == "HOLD":
            return self._reject(Message("risk_proposal_is_hold"))
        if proposal.action not in {"BUY", "SELL"}:
            return self._reject(Message("risk_unsupported_action", {"action": proposal.action}))
        if proposal.confidence < Decimal(str(risk["min_ai_confidence"])):
            return self._reject(Message("risk_confidence_too_low"))
        if risk_state.kill_switch_active:
            return self._reject(Message("risk_kill_switch", {"summary": risk_state.summary}))
        if risk_state.cooldown_active:
            return self._reject(Message("risk_cooldown", {"summary": risk_state.summary}))
        if risk_state.trades_today >= int(risk["max_trades_per_day"]):
            return self._reject(Message("risk_daily_trade_limit"))
        if risk_state.daily_loss_pct >= Decimal(str(risk["max_daily_loss_pct"])):
            return self._reject(Message("risk_daily_loss_limit"))
        if risk_state.weekly_loss_pct >= Decimal(str(risk["max_weekly_loss_pct"])):
            return self._reject(Message("risk_weekly_loss_limit"))
        # Outside the consensus block on purpose. Every other trend check sits
        # behind `consensus.enabled` or `skip_consensus`, and this one is not a
        # view about the market - it is the absence of the data those views are
        # computed from. A caller that has good reason to skip consensus still
        # has no reason to buy a pair whose averages are made of three weeks.
        if proposal.action == "BUY":
            snapshot = next((item for item in snapshots if item.symbol == proposal.symbol), None)
            if snapshot is not None and snapshot.trend_regime == TREND_INSUFFICIENT_HISTORY:
                return self._reject(
                    Message("risk_insufficient_history", {"symbol": proposal.symbol})
                )
        if not skip_consensus:
            consensus_reason = self._consensus_rejection(proposal, snapshots)
            if consensus_reason is not None:
                return self._reject(consensus_reason)
        if self.config["orders"]["require_stop_loss"] and proposal.stop_loss_pct <= 0:
            return self._reject(Message("risk_stop_loss_required"))

        binding, adjusted = self._size(proposal, portfolio_value, spendable_quote)
        approved = Message(
            "risk_approved" if not skip_consensus else "risk_approved_skip_consensus"
        )
        return RiskDecision(
            True,
            render_message(approved),
            adjusted,
            reason_message=approved,
            binding_limit=binding,
        )

    def _size(
        self,
        proposal: TradeProposal,
        portfolio_value: Decimal | None,
        spendable_quote: Decimal | None,
    ) -> tuple[str, Decimal]:
        """The smallest ceiling that applies, and which one it was."""
        return min(self.sizing_caps(proposal, portfolio_value, spendable_quote), key=lambda cap: cap[1])

    def sizing_caps(
        self,
        proposal: TradeProposal,
        portfolio_value: Decimal | None,
        spendable_quote: Decimal | None,
    ) -> list[tuple[str, Decimal]]:
        """Every ceiling that applies to this order, named.

        Every entry is a ceiling and the answer is their minimum, so adding one
        here can only ever shrink an approved order. That property is what
        makes this safe to extend: no limit added to this list can authorise
        something the same config would have refused before it existed.

        Public because "why is the order this size" is a question worth being
        able to ask without re-deriving the arithmetic.
        """
        risk = self.config["risk"]
        # `earn.max_redeem_per_run_usdt` used to sit here, and does not belong:
        # it is how much Flexible Earn one run may release, not how large a
        # trade may be, and it applied even when the money came entirely from
        # Spot and no redeem was going to happen. Where it is genuinely
        # relevant it is already accounted for - `spendable_quote` is built
        # from exactly these redeem bounds - so keeping it here both
        # double-counted and truncated confirmed first-portfolio tranches to a
        # number the user never agreed to.
        caps: list[tuple[str, Decimal]] = [("proposal", proposal.quote_amount_usdt)]
        if portfolio_value is not None and portfolio_value > 0:
            # The portfolio-relative companion to strategy.quote_amount_usdt,
            # which is a flat number and so means something different on a 500
            # account than on a 50,000 one. Absent from older configs, where
            # 100% leaves the flat number in charge exactly as before.
            trade_pct = self.config["strategy"].get("max_trade_pct_of_portfolio", 100)
            caps.append(("trade_size_pct", self._pct_of(portfolio_value, trade_pct)))
        if portfolio_value is not None and portfolio_value > 0:
            caps.append(
                ("total_trading_capital", self._pct_of(portfolio_value, risk["max_total_trading_capital_pct"]))
            )
            caps.append(
                ("position_per_asset", self._pct_of(portfolio_value, risk["max_position_pct_per_asset"]))
            )
            # How much can be bought so that the stop loss costs at most
            # max_risk_per_trade_pct of the portfolio. Skipped without a stop:
            # there is no defined loss to size against, and `orders
            # .require_stop_loss` has already had its say above.
            stop_loss_pct = Decimal(str(proposal.stop_loss_pct))
            if stop_loss_pct > 0:
                budget = self._pct_of(portfolio_value, risk["max_risk_per_trade_pct"])
                caps.append(("risk_per_trade", budget / (stop_loss_pct / Decimal("100"))))
        if spendable_quote is not None:
            caps.append(("funding", max(Decimal("0"), spendable_quote)))
        return caps

    @staticmethod
    def _pct_of(value: Decimal, percent: object) -> Decimal:
        return value * Decimal(str(percent)) / Decimal("100")

    def _reject(self, message: Message) -> RiskDecision:
        """Render English once, here, so the string cannot drift from the key."""
        return RiskDecision(False, render_message(message), Decimal("0"), reason_message=message)

    def _consensus_rejection(
        self,
        proposal: TradeProposal,
        snapshots: list[MarketSnapshot],
    ) -> Message | None:
        consensus = self.config.get("consensus", {})
        if not consensus.get("enabled", True) or proposal.action != "BUY":
            return None
        snapshot = next((item for item in snapshots if item.symbol == proposal.symbol), None)
        if snapshot is None:
            return Message("risk_no_snapshot", {"symbol": proposal.symbol})
        if consensus.get("require_risk_on", True) and snapshot.trend_regime != "RISK_ON":
            return Message("risk_trend_not_risk_on", {"symbol": proposal.symbol, "regime": snapshot.trend_regime})
        if consensus.get("require_price_above_ema200", True) and snapshot.price <= snapshot.ema200:
            return Message("risk_below_ema200", {"symbol": proposal.symbol})
        min_rsi = Decimal(str(consensus.get("min_rsi14", "45")))
        max_rsi = Decimal(str(consensus.get("max_rsi14", "68")))
        if not min_rsi <= snapshot.rsi14 <= max_rsi:
            return Message(
                "risk_rsi_outside_band",
                {"symbol": proposal.symbol, "value": display(snapshot.rsi14),
                 "minimum": str(min_rsi), "maximum": str(max_rsi)},
            )
        if consensus.get("require_rising_volume", False) and snapshot.volume_trend != "rising":
            return Message("risk_volume_not_rising", {"symbol": proposal.symbol, "trend": snapshot.volume_trend})
        return None
