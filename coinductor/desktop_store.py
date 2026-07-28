from __future__ import annotations

from datetime import datetime, timedelta, UTC
from decimal import Decimal, InvalidOperation
from pathlib import Path
import re
import sqlite3

from trading_agent.manual_steps import manual_steps_from_json
from trading_agent.storage import apply_connection_pragmas, column_or_null, table_columns, table_exists

from .models import DesktopSnapshot
from .report_summary import ReportSummaryReader


class DesktopStore:
    def __init__(
        self,
        database_path: str | Path = "work/trading_agent.sqlite3",
        reports_dir: str | Path = "outputs/reports",
    ):
        self.database_path = Path(database_path)
        self.reports_dir = Path(reports_dir)
        self.summary_reader = ReportSummaryReader()

    def load(self) -> DesktopSnapshot:
        if not self.database_path.exists():
            return DesktopSnapshot(None, (), (), ())
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        # The UI reads while a run may be writing; without WAL and a busy timeout
        # that read fails outright with "database is locked".
        apply_connection_pragmas(connection)
        try:
            latest = self._latest_real_run(connection)
            latest_result = None
            portfolio: tuple[dict[str, str], ...] = ()
            strategies: tuple[dict[str, str], ...] = ()
            position_protection: dict[str, object] | None = None
            live_action_lifecycle: dict[str, object] | None = None
            active_strategies: tuple[dict[str, object], ...] = ()
            active_strategies_summary = "No active strategies are registered."
            next_review: dict[str, object] | None = None
            earn_redeem: dict[str, object] | None = None
            has_ready_live_preview = False
            if latest is not None:
                report_path = self._report_path(latest)
                if report_path is not None and report_path.exists():
                    latest_result = self.summary_reader.read(
                        int(latest["id"]),
                        str(latest["status"]),
                        str(report_path),
                    )
                    trade_proposal = self._trade_proposal(connection, int(latest["id"]))
                    latest_result = latest_result.__class__(**{**latest_result.__dict__, "trade_proposal": trade_proposal})
                portfolio = self._portfolio(connection, int(latest["id"]))
                strategies = self._strategies(connection, int(latest["id"]))
                position_protection = self._position_protection(connection, int(latest["id"]))
                has_ready_live_preview = self._has_ready_live_preview(connection)
                live_action_lifecycle = self._live_action_lifecycle(connection)
                active_strategies, active_strategies_summary = self._active_strategies(connection, int(latest["id"]))
                next_review = self._next_review(
                    connection,
                    int(latest["id"]),
                    str(latest["started_at"] or ""),
                    strategies,
                )
                earn_redeem = self._earn_redeem(connection, int(latest["id"]))
            history = self._history(connection)
            return DesktopSnapshot(
                latest_result,
                portfolio,
                strategies,
                history,
                position_protection,
                has_ready_live_preview,
                live_action_lifecycle,
                active_strategies,
                active_strategies_summary,
                next_review,
                earn_redeem,
            )
        finally:
            connection.close()

    def _latest_real_run(self, connection: sqlite3.Connection) -> sqlite3.Row | None:
        return connection.execute(
            """
            select r.*, mr.status as data_status
            from runs r
            join market_research_reports mr on mr.run_id = r.id
            where r.status = 'OK' and mr.status != 'MOCK'
            order by r.id desc
            limit 1
            """
        ).fetchone()

    def _portfolio(self, connection: sqlite3.Connection, run_id: int) -> tuple[dict[str, str], ...]:
        rows = connection.execute(
            """
            select asset, role, total_value_usdt, allocation_pct, spot_value_usdt,
                   flexible_value_usdt, locked_value_usdt, rebalance_action
            from portfolio_valuations
            where run_id = ?
            order by cast(total_value_usdt as real) desc
            """,
            (run_id,),
        ).fetchall()
        return tuple(
            {
                "asset": str(row["asset"]),
                "role": str(row["role"] or "UNCLASSIFIED"),
                "value": self._money(row["total_value_usdt"]),
                "allocation": self._percent(row["allocation_pct"]),
                "spot": self._money(row["spot_value_usdt"]),
                "flexible": self._money(row["flexible_value_usdt"]),
                "locked": self._money(row["locked_value_usdt"]),
                "action": str(row["rebalance_action"] or "HOLD"),
            }
            for row in rows
        )

    def _trade_proposal(self, connection: sqlite3.Connection, run_id: int) -> dict[str, str] | None:
        if not self._table_exists(connection, "ai_proposals"):
            return None
        row = connection.execute(
            """
            select symbol, action, confidence, quote_amount_usdt, reason
            from ai_proposals where run_id = ?
            """,
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        return {
            "symbol": str(row["symbol"] or ""),
            "action": str(row["action"] or ""),
            "confidence": str(row["confidence"] or ""),
            "quoteAmount": self._money(row["quote_amount_usdt"]),
            "reason": str(row["reason"] or ""),
        }

    def _strategies(self, connection: sqlite3.Connection, run_id: int) -> tuple[dict[str, object], ...]:
        strategies: list[dict[str, object]] = []
        if self._table_exists(connection, "grid_recommendations"):
            grid_columns = self._columns(connection, "grid_recommendations")
            grid = connection.execute(
                f"""
                select symbol, market_status, deployment_allowed, score, investment_usdt, reason,
                       {self._column_expr(grid_columns, "range_low")}, {self._column_expr(grid_columns, "range_high")},
                       {self._column_expr(grid_columns, "grid_count")}, {self._column_expr(grid_columns, "stop_loss_price")},
                       {self._column_expr(grid_columns, "take_profit_price")}, {self._column_expr(grid_columns, "estimated_grid_spacing_pct")},
                       {self._column_expr(grid_columns, "blockers")},
                       {self._column_expr(grid_columns, "manual_steps")}
                from grid_recommendations where run_id = ?
                """,
                (run_id,),
            ).fetchone()
            if grid is not None:
                symbol = str(grid["symbol"] or "")
                entry_price = self._market_price_for_run(connection, run_id, symbol)
                strategies.append(
                    {
                        "type": "Spot Grid",
                        "name": symbol or "No candidate",
                        "status": "READY" if grid["deployment_allowed"] else str(grid["market_status"] or "WATCH"),
                        "capital": self._money(grid["investment_usdt"]),
                        "allowed": "Ready" if grid["deployment_allowed"] else "Watched" if str(grid["market_status"] or "").upper() == "WATCH" else "Blocked",
                        "detail": str(grid["reason"] or ""),
                        "parameters": (
                            {"label": "Symbol", "value": str(grid["symbol"] or "")},
                            {"label": "Range", "value": self._range(grid["range_low"], grid["range_high"])},
                            {"label": "Grids", "value": str(grid["grid_count"] or "")},
                            {"label": "Investment", "value": self._money(grid["investment_usdt"])},
                            {"label": "Spacing", "value": self._percent(grid["estimated_grid_spacing_pct"])},
                            {"label": "TP / SL", "value": self._range(grid["take_profit_price"], grid["stop_loss_price"])},
                        ),
                        "blockers": self._line_values(grid["blockers"]),
                        "manualSteps": self._manual_step_specs(grid["manual_steps"]),
                        "registrationSuggestion": {
                            "available": bool(symbol),
                            "name": f"{symbol} Grid" if symbol else "",
                            "symbol": symbol,
                            "rangeLow": self._number(grid["range_low"]),
                            "rangeHigh": self._number(grid["range_high"]),
                            "gridCount": str(grid["grid_count"] or ""),
                            "gridType": "ARITHMETIC",
                            "investment": self._number(grid["investment_usdt"]),
                            "entryPrice": self._number(entry_price) if entry_price is not None else "",
                            "stopLoss": self._number(grid["stop_loss_price"]),
                            "takeProfit": self._number(grid["take_profit_price"]),
                            "sourceRun": str(run_id),
                        },
                    }
                )
        if self._table_exists(connection, "rebalancing_bot_recommendations"):
            rebalance_columns = self._columns(connection, "rebalancing_bot_recommendations")
            rebalance = connection.execute(
                f"""
                select deployment_allowed, mode, threshold_pct, investment_usdt, summary,
                       {self._column_expr(rebalance_columns, "blockers")},
                       {self._column_expr(rebalance_columns, "manual_steps")}
                from rebalancing_bot_recommendations where run_id = ?
                """,
                (run_id,),
            ).fetchone()
            if rebalance is not None:
                basket = self._rebalancing_basket(connection, run_id)
                strategies.append(
                    {
                        "type": "Rebalancing",
                        "name": str(rebalance["mode"] or "THRESHOLD"),
                        "status": "READY" if rebalance["deployment_allowed"] else "BLOCKED",
                        "capital": self._money(rebalance["investment_usdt"]),
                        "allowed": "Ready" if rebalance["deployment_allowed"] else "Blocked",
                        "detail": str(rebalance["summary"] or ""),
                        "parameters": (
                            {"label": "Mode", "value": str(rebalance["mode"] or "THRESHOLD")},
                            {"label": "Investment", "value": self._money(rebalance["investment_usdt"])},
                            {"label": "Trigger", "value": f"By ratio {self._percent(rebalance['threshold_pct'])}"},
                            {"label": "Basket", "value": basket},
                        ),
                        "blockers": self._line_values(rebalance["blockers"]),
                        "manualSteps": self._manual_step_specs(rebalance["manual_steps"]),
                        "registrationSuggestion": self._rebalancing_registration_suggestion(
                            connection,
                            run_id,
                            rebalance["investment_usdt"],
                            rebalance["threshold_pct"],
                        ),
                    }
                )
        return tuple(strategies)

    def _position_protection(self, connection: sqlite3.Connection, run_id: int) -> dict[str, object] | None:
        if not self._table_exists(connection, "oco_protection_orders"):
            return None
        row = connection.execute(
            """
            select intent_id, symbol, status, adjusted_quantity, take_profit_price,
                   stop_loss_stop_price, estimated_take_profit_quote, estimated_stop_quote,
                   submitted, order_list_id, confirmation_required, reason, message
            from oco_protection_orders
            where run_id = ?
            order by rowid desc
            limit 1
            """,
            (run_id,),
        ).fetchone()
        if row is None:
            return None
        status = str(row["status"] or "UNKNOWN").upper()
        submitted = bool(row["submitted"])
        if submitted or status == "PROTECTED":
            tone = "ready"
            display_status = "Protected"
        elif status == "READY":
            tone = "ready"
            display_status = "Ready"
        else:
            tone = "blocked"
            display_status = "Blocked"
        return {
            "title": "Position protection",
            "status": display_status,
            "tone": tone,
            "detail": str(row["message"] or row["reason"] or "No protection detail was recorded."),
            "parameters": (
                {"label": "Symbol", "value": str(row["symbol"] or "")},
                {"label": "Quantity", "value": str(row["adjusted_quantity"] or "")},
                {"label": "Take profit", "value": str(row["take_profit_price"] or "")},
                {"label": "Stop loss", "value": str(row["stop_loss_stop_price"] or "")},
                {"label": "TP estimate", "value": self._money(row["estimated_take_profit_quote"])},
                {"label": "SL estimate", "value": self._money(row["estimated_stop_quote"])},
            ),
            "canSubmitOco": status == "READY" and not submitted,
            "confirmationRequired": str(row["confirmation_required"] or "CONFIRM_MAINNET_OCO"),
            "intentId": str(row["intent_id"] or ""),
            "orderListId": str(row["order_list_id"] or ""),
        }

    def _earn_redeem(self, connection: sqlite3.Connection, run_id: int) -> dict[str, object] | None:
        if not self._table_exists(connection, "earn_redeem_plans"):
            return None
        if "intent_id" not in self._columns(connection, "earn_redeem_plans"):
            return None
        row = connection.execute(
            """
            select intent_id, enabled, asset, amount, status, product_id, redeem_type,
                   submitted, confirmation_required, message
            from earn_redeem_plans
            where run_id = ?
            order by rowid desc
            limit 1
            """,
            (run_id,),
        ).fetchone()
        if row is None or not bool(row["enabled"]):
            return None
        status = str(row["status"] or "NOT_NEEDED").upper()
        if status == "NOT_NEEDED":
            return None
        submitted = bool(row["submitted"])
        if submitted or status == "SUBMITTED":
            tone = "ready"
            display_status = "Submitted"
        elif status == "PREVIEW_READY":
            tone = "ready"
            display_status = "Ready"
        else:
            tone = "blocked"
            display_status = "Blocked"
        return {
            "title": "Earn redeem",
            "status": display_status,
            "tone": tone,
            "detail": str(row["message"] or "No Earn redeem detail was recorded."),
            "parameters": (
                {"label": "Asset", "value": str(row["asset"] or "")},
                {"label": "Amount", "value": self._money(row["amount"])},
                {"label": "Product", "value": str(row["product_id"] or "")},
                {"label": "Redeem type", "value": str(row["redeem_type"] or "")},
            ),
            "canSubmitEarnRedeem": status == "PREVIEW_READY" and not submitted,
            "confirmationRequired": str(row["confirmation_required"] or "CONFIRM_EARN_REDEEM"),
            "intentId": str(row["intent_id"] or ""),
        }

    def _has_ready_live_preview(self, connection: sqlite3.Connection) -> bool:
        if not self._table_exists(connection, "live_orders"):
            return False
        row = connection.execute(
            """
            select 1
            from live_orders
            where status = 'PREVIEW_READY' and submitted = 0
            limit 1
            """
        ).fetchone()
        return row is not None

    def _live_action_lifecycle(self, connection: sqlite3.Connection) -> dict[str, object] | None:
        required_live_columns = {
            "run_id", "intent_id", "symbol", "side", "status", "submitted",
            "order_id", "executed_quantity", "cumulative_quote_qty",
        }
        if not self._table_exists(connection, "live_orders"):
            return None
        if not required_live_columns.issubset(self._columns(connection, "live_orders")):
            return None

        buy = connection.execute(
            """
            select live.*, runs.started_at
            from live_orders live
            left join runs on runs.id = live.run_id
            where live.side = 'BUY'
              and live.submitted = 1
              and live.status not in ('SUBMIT_ERROR', 'SUBMIT_SKIPPED')
            order by live.run_id desc, live.rowid desc
            limit 1
            """
        ).fetchone()
        if buy is None:
            return None

        intent_id = str(buy["intent_id"] or "")
        symbol = str(buy["symbol"] or "")
        buy_status = str(buy["status"] or "SUBMITTED").upper()
        sell = connection.execute(
            """
            select live.*, runs.started_at
            from live_orders live
            left join runs on runs.id = live.run_id
            where live.intent_id = ? and live.side = 'SELL'
              and live.submitted = 1 and live.status = 'FILLED'
            order by live.run_id desc, live.rowid desc
            limit 1
            """,
            (f"sell-{intent_id}",),
        ).fetchone()

        oco = None
        required_oco_columns = {
            "run_id", "intent_id", "status", "submitted", "order_list_id",
            "take_profit_price", "stop_loss_stop_price",
        }
        if self._table_exists(connection, "oco_protection_orders") and required_oco_columns.issubset(
            self._columns(connection, "oco_protection_orders")
        ):
            oco = connection.execute(
                """
                select protection.*, runs.started_at
                from oco_protection_orders protection
                left join runs on runs.id = protection.run_id
                where protection.intent_id = ?
                order by protection.run_id desc, protection.rowid desc
                limit 1
                """,
                (f"oco-{intent_id}",),
            ).fetchone()

        oco_check = None
        if oco is not None and self._table_exists(connection, "oco_status_checks"):
            required_check_columns = {
                "run_id", "intent_id", "order_list_id", "list_order_status", "list_status_type",
            }
            if required_check_columns.issubset(self._columns(connection, "oco_status_checks")):
                oco_check = connection.execute(
                    """
                    select status_check.*, runs.started_at
                    from oco_status_checks status_check
                    left join runs on runs.id = status_check.run_id
                    where status_check.intent_id = ? or status_check.order_list_id = ?
                    order by status_check.run_id desc, status_check.rowid desc
                    limit 1
                    """,
                    (str(oco["intent_id"] or ""), str(oco["order_list_id"] or "")),
                ).fetchone()

        quantity = self._decimal(buy["executed_quantity"])
        buy_quote = self._decimal(buy["cumulative_quote_qty"])
        entry_price = buy_quote / quantity if quantity > 0 else Decimal("0")
        current_price = self._latest_market_price(connection, symbol)
        current_value = quantity * current_price if quantity > 0 and current_price is not None else None
        open_pnl = current_value - buy_quote if current_value is not None else None

        sell_quote = self._decimal(sell["cumulative_quote_qty"]) if sell is not None else None
        sell_quantity = self._decimal(sell["executed_quantity"]) if sell is not None else None
        allocated_buy_quote = buy_quote
        if sell_quantity is not None and quantity > 0:
            allocated_buy_quote = buy_quote * min(sell_quantity, quantity) / quantity
        realized_pnl = sell_quote - allocated_buy_quote if sell_quote is not None else None

        protection_submitted = bool(oco["submitted"]) if oco is not None else False
        protection_status = str(oco["status"] or "") if oco is not None else ""
        list_order_status = str(oco_check["list_order_status"] or "") if oco_check is not None else ""
        list_status_type = str(oco_check["list_status_type"] or "") if oco_check is not None else ""
        protection_active = protection_submitted and sell is None and list_order_status.upper() not in {
            "ALL_DONE", "DONE", "FILLED", "REJECT", "EXPIRED",
        }

        if sell is not None:
            status = "Closed"
            tone = "ready"
            detail = "The protected position cycle is closed and the filled SELL has been reconciled locally."
        elif protection_active:
            status = "Protected"
            tone = "ready"
            detail = "The BUY is filled and Binance-hosted OCO protection is active while Coinductor is offline."
        elif buy_status == "FILLED":
            status = "Protection needed"
            tone = "watch"
            detail = "The BUY is filled, but active Binance-hosted OCO protection has not been confirmed yet."
        else:
            status = "Submitted"
            tone = "watch"
            detail = "The BUY was submitted and its latest locally recorded fill status is still being monitored."

        last_checked = self._latest_timestamp(buy, oco, oco_check, sell)
        pnl = realized_pnl if sell is not None else open_pnl
        pnl_basis = allocated_buy_quote if sell is not None else buy_quote
        pnl_pct = pnl * Decimal("100") / pnl_basis if pnl is not None and pnl_basis > 0 else None
        stages = (
            self._lifecycle_stage("Submitted", "Done", f"BUY order {buy['order_id'] or 'ID pending'}"),
            self._lifecycle_stage(
                "Filled",
                "Done" if buy_status == "FILLED" else "Active",
                f"{self._number(quantity)} {self._base_asset(symbol)}" if quantity > 0 else "Awaiting executed quantity",
            ),
            self._lifecycle_stage(
                "Protected",
                "Done" if protection_submitted else "Action needed" if buy_status == "FILLED" else "Pending",
                f"OCO {oco['order_list_id']}" if protection_submitted and oco is not None else "OCO not active",
            ),
            self._lifecycle_stage(
                "Closed",
                "Done" if sell is not None else "Pending",
                f"SELL order {sell['order_id']}" if sell is not None else "Waiting for an exit leg",
            ),
        )
        return {
            "title": "Live position lifecycle",
            "status": status,
            "tone": tone,
            "detail": detail,
            "parameters": (
                {"label": "Symbol", "value": symbol},
                {"label": "BUY order ID", "value": str(buy["order_id"] or "Pending")},
                {"label": "Quantity", "value": self._number(quantity)},
                {"label": "Entry price", "value": self._number(entry_price)},
                {"label": "Current / exit price", "value": self._number(current_price if sell is None else self._safe_price(sell_quote, sell_quantity))},
                {"label": "PnL (fees excluded)", "value": self._pnl(pnl, pnl_pct)},
                {"label": "Take profit", "value": self._number(oco["take_profit_price"] if oco is not None else None)},
                {"label": "Stop loss", "value": self._number(oco["stop_loss_stop_price"] if oco is not None else None)},
                {"label": "OCO list ID", "value": str(oco["order_list_id"] or "Not active") if oco is not None else "Not active"},
                {"label": "OCO exchange status", "value": " / ".join(part for part in (list_status_type, list_order_status) if part) or protection_status or "Not checked"},
                {"label": "Last synchronized", "value": last_checked or "Not recorded"},
            ),
            "lifecycleSteps": stages,
            "primaryLabel": "View lifecycle",
            "actionCode": "REVIEW_LIFECYCLE",
        }

    def _active_strategies(
        self,
        connection: sqlite3.Connection,
        run_id: int,
    ) -> tuple[tuple[dict[str, object], ...], str]:
        items: list[dict[str, object]] = []
        if self._table_exists(connection, "active_grid_evaluations"):
            columns = self._columns(connection, "active_grid_evaluations")
            required = {"run_id", "name", "symbol", "state", "recommendation"}
            if required.issubset(columns):
                rows = connection.execute(
                    f"""
                    select name, symbol, range_low, range_high, investment_usdt, current_price,
                           state, distance_to_lower_pct, distance_to_upper_pct, recommendation,
                           {self._column_expr(columns, "binance_bot_id")},
                           {self._column_expr(columns, "grid_count")},
                           {self._column_expr(columns, "grid_type")},
                           {self._column_expr(columns, "entry_price")},
                           {self._column_expr(columns, "stop_loss_price")},
                           {self._column_expr(columns, "take_profit_price")},
                           {self._column_expr(columns, "age_days")}
                    from active_grid_evaluations
                    where run_id = ?
                    order by name
                    """,
                    (run_id,),
                ).fetchall()
                items.extend(self._active_grid_item(row) for row in rows)

        if self._table_exists(connection, "active_rebalancing_evaluations"):
            columns = self._columns(connection, "active_rebalancing_evaluations")
            required = {"run_id", "name", "state", "recommendation"}
            if required.issubset(columns):
                rows = connection.execute(
                    """
                    select name, binance_bot_id, assets, target_weights_pct, current_weights_pct,
                           investment_usdt, threshold_pct, max_drift_pct, state, age_days,
                           recommendation
                    from active_rebalancing_evaluations
                    where run_id = ?
                    order by name
                    """,
                    (run_id,),
                ).fetchall()
                items.extend(self._active_rebalancing_item(row) for row in rows)

        if not items:
            return (), "No registered active Grid or Rebalancing bots were evaluated in the latest run."
        healthy = len([item for item in items if item["health"] == "Healthy"])
        review = len([item for item in items if item["health"] == "Review"])
        action = len(items) - healthy - review
        return tuple(items), f"{len(items)} active strategy(s): {healthy} healthy, {review} to review, {action} requiring action."

    def _next_review(
        self,
        connection: sqlite3.Connection,
        run_id: int,
        started_at: str,
        strategies: tuple[dict[str, object], ...],
    ) -> dict[str, object] | None:
        if not self._table_exists(connection, "next_run_recommendations"):
            return None
        required = {"run_id", "run_again_in_hours", "urgency", "reason", "triggers"}
        if not required.issubset(self._columns(connection, "next_run_recommendations")):
            return None
        row = connection.execute(
            """
            select run_again_in_hours, urgency, reason, triggers
            from next_run_recommendations where run_id = ? order by rowid desc limit 1
            """,
            (run_id,),
        ).fetchone()
        if row is None:
            return None

        hours = max(0, int(row["run_again_in_hours"] or 0))
        triggers = list(self._line_values(row["triggers"]))
        structural_terms = (
            "funding",
            "capital",
            "protected asset",
            "minimum investment",
            "uncovered",
            "insufficient",
            "liquidity",
            "redeem",
        )
        manual_steps: list[str] = []
        market_conditions: list[str] = []
        for strategy in strategies:
            strategy_type = str(strategy.get("type", "Strategy"))
            # Blockers used to be scanned out of the parameter tiles by label.
            # They have their own key now, because a sentence cannot live in a
            # fixed-width tile - this list is what the panel is built from.
            for blocker in strategy.get("blockers", ()):
                item = f"{strategy_type}: {blocker}"
                if any(term in str(blocker).lower() for term in structural_terms):
                    manual_steps.append(item)
                else:
                    market_conditions.append(item)

        scheduled_at = self._scheduled_review(started_at, hours)
        due_now = scheduled_at is not None and scheduled_at <= datetime.now(UTC)
        # `state` is the identifier; status/headline/timing are its English
        # rendering. The controller re-renders them in the user's language,
        # which it cannot do from prose alone.
        if manual_steps:
            state = "MANUAL_STEP"
            status = "Manual step before rerun"
            tone = "blocked"
            headline = "A fresh run can update market data, but it cannot remove the listed funding or configuration blocker."
        elif hours == 0:
            state = "REVIEW_NOW"
            status = "Review now"
            tone = "watch"
            headline = "The latest run produced an action that should be reviewed before waiting for another scheduled check."
        elif due_now:
            state = "DUE_NOW"
            status = "Review due now"
            tone = "watch"
            headline = "The recommended review interval has elapsed. Run a fresh analysis when convenient."
        else:
            state = "SCHEDULED"
            status = f"Check again in {hours} hours"
            tone = "watch"
            headline = "No immediate action is required. Wait for the suggested interval unless an earlier trigger occurs."

        return {
            "state": state,
            "status": status,
            "tone": tone,
            "headline": headline,
            "hours": hours,
            "timing": "After the manual step" if manual_steps else "Now" if due_now or hours == 0 else f"In {hours} hours",
            "scheduledAt": self._format_scheduled_review(scheduled_at),
            "reason": str(row["reason"] or "No next-run reason was recorded."),
            "triggers": list(dict.fromkeys(triggers + market_conditions)),
            "manualSteps": list(dict.fromkeys(manual_steps)),
            "sourceRun": str(run_id),
            "urgency": str(row["urgency"] or "NORMAL").replace("_", " ").title(),
        }

    def _scheduled_review(self, started_at: str, hours: int) -> datetime | None:
        if not started_at:
            return None
        try:
            started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        except ValueError:
            return None
        if started.tzinfo is None:
            started = started.replace(tzinfo=UTC)
        return started.astimezone(UTC) + timedelta(hours=hours)

    def _format_scheduled_review(self, value: datetime | None) -> str:
        if value is None:
            return "Not available"
        return self._local_timestamp(value)

    def _local_timestamp(self, value: datetime, seconds: bool = False) -> str:
        local_value = value.astimezone()
        offset = local_value.utcoffset() or timedelta(0)
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        offset_hours, offset_minutes = divmod(abs(total_minutes), 60)
        pattern = "%Y-%m-%d %H:%M:%S" if seconds else "%Y-%m-%d %H:%M"
        return f"{local_value:{pattern}} UTC{sign}{offset_hours:02d}:{offset_minutes:02d}"

    def _local_started_at(self, value: object) -> str:
        """Render a run's start time in the reader's timezone.

        SQLite's `default current_timestamp` writes UTC with no offset, and Run
        History printed that string straight out - so every run appeared to
        have happened hours before it did, while the Action Plan's next-review
        line (which already converted) disagreed with it on the same screen.
        """
        text = str(value or "").strip()
        if not text:
            return ""
        try:
            parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return text
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return self._local_timestamp(parsed, seconds=True)

    def _active_grid_item(self, row: sqlite3.Row) -> dict[str, object]:
        state = str(row["state"] or "UNKNOWN_PRICE").upper()
        health, tone = self._strategy_health(state)
        return {
            "type": "Spot Grid",
            "localStatus": "Active",
            "name": str(row["name"] or "Unnamed Grid"),
            "botId": str(row["binance_bot_id"] or "Not recorded"),
            "health": health,
            "tone": tone,
            "state": self._strategy_state_label(state),
            "recommendation": str(row["recommendation"] or "Review the strategy in Binance."),
            "parameters": (
                {"label": "Symbol", "value": str(row["symbol"] or "")},
                {"label": "Current price", "value": self._number(row["current_price"])},
                {"label": "Range", "value": self._range(row["range_low"], row["range_high"])},
                {"label": "Investment", "value": self._money(row["investment_usdt"])},
                {"label": "Grid setup", "value": f"{row['grid_count'] or '-'} / {row['grid_type'] or '-'}"},
                {"label": "Age", "value": f"{self._number(row['age_days'])} days" if row["age_days"] not in (None, "") else "-"},
                {"label": "Distance to range", "value": f"Lower {self._percent(row['distance_to_lower_pct'])}, upper {self._percent(row['distance_to_upper_pct'])}"},
                {"label": "Entry", "value": self._number(row["entry_price"])},
                {"label": "TP / SL", "value": self._range(row["take_profit_price"], row["stop_loss_price"])},
            ),
        }

    def _active_rebalancing_item(self, row: sqlite3.Row) -> dict[str, object]:
        state = str(row["state"] or "UNKNOWN_PRICE").upper()
        health, tone = self._strategy_health(state)
        assets = self._line_values(row["assets"])
        targets = self._line_values(row["target_weights_pct"])
        currents = self._line_values(row["current_weights_pct"])
        target_basket = ", ".join(
            f"{asset} {self._percent(weight)}" for asset, weight in zip(assets, targets)
        )
        current_basket = ", ".join(
            f"{asset} {self._percent(weight)}" for asset, weight in zip(assets, currents)
        )
        return {
            "type": "Rebalancing",
            "localStatus": "Active",
            "name": str(row["name"] or "Unnamed Rebalancing Bot"),
            "botId": str(row["binance_bot_id"] or "Not recorded"),
            "health": health,
            "tone": tone,
            "state": self._strategy_state_label(state),
            "recommendation": str(row["recommendation"] or "Review the strategy in Binance."),
            "parameters": (
                {"label": "Assets", "value": ", ".join(assets)},
                {"label": "Target basket", "value": target_basket or "-"},
                {"label": "Current estimate", "value": current_basket or "-"},
                {"label": "Investment", "value": self._money(row["investment_usdt"])},
                {"label": "Rebalance threshold", "value": self._percent(row["threshold_pct"])},
                {"label": "Maximum drift", "value": self._percent(row["max_drift_pct"])},
                {"label": "Age", "value": f"{self._number(row['age_days'])} days" if row["age_days"] not in (None, "") else "-"},
            ),
        }

    def _strategy_health(self, state: str) -> tuple[str, str]:
        if state in {"IN_RANGE", "WITHIN_THRESHOLD"}:
            return "Healthy", "ready"
        if state in {"NEAR_LOWER", "NEAR_UPPER"}:
            return "Review", "watch"
        return "Action required", "blocked"

    def _strategy_state_label(self, state: str) -> str:
        return state.replace("_", " ").title()

    def _line_values(self, value: object) -> tuple[str, ...]:
        return tuple(part.strip() for part in str(value or "").splitlines() if part.strip())

    def _manual_step_specs(self, value: object) -> list[dict[str, object]]:
        """Hand the manual steps on unrendered so the controller can localize.

        The stored column is JSON from 0.1.4 onward and newline-separated
        English before that; manual_steps_from_json absorbs both, and an
        unrecognised key renders as itself, so a run recorded by an older
        version keeps showing exactly what it always showed.
        """
        return [
            {"key": step.key, "params": dict(step.params)}
            for step in manual_steps_from_json(str(value or ""))
        ]

    def _latest_market_price(self, connection: sqlite3.Connection, symbol: str) -> Decimal | None:
        if not self._table_exists(connection, "market_snapshots"):
            return None
        if not {"run_id", "symbol", "price"}.issubset(self._columns(connection, "market_snapshots")):
            return None
        row = connection.execute(
            "select price from market_snapshots where symbol = ? order by run_id desc, rowid desc limit 1",
            (symbol,),
        ).fetchone()
        return self._decimal(row["price"]) if row is not None else None

    def _market_price_for_run(self, connection: sqlite3.Connection, run_id: int, symbol: str) -> Decimal | None:
        if not self._table_exists(connection, "market_snapshots"):
            return None
        if not {"run_id", "symbol", "price"}.issubset(self._columns(connection, "market_snapshots")):
            return None
        row = connection.execute(
            "select price from market_snapshots where run_id = ? and symbol = ? order by rowid desc limit 1",
            (run_id, symbol),
        ).fetchone()
        return self._decimal(row["price"]) if row is not None else None

    def _lifecycle_stage(self, label: str, status: str, detail: str) -> dict[str, str]:
        return {"label": label, "status": status, "detail": detail}

    def _latest_timestamp(self, *rows: sqlite3.Row | None) -> str:
        values = [str(row["started_at"] or "") for row in rows if row is not None and "started_at" in row.keys()]
        return max((value for value in values if value), default="")

    def _decimal(self, value: object) -> Decimal:
        try:
            return Decimal(str(value or "0"))
        except (InvalidOperation, ValueError):
            return Decimal("0")

    def _safe_price(self, quote: Decimal | None, quantity: Decimal | None) -> Decimal | None:
        if quote is None or quantity is None or quantity <= 0:
            return None
        return quote / quantity

    def _number(self, value: object) -> str:
        if value in (None, ""):
            return "-"
        number = self._decimal(value)
        rendered = f"{number:.8f}".rstrip("0").rstrip(".")
        return rendered or "0"

    def _pnl(self, value: Decimal | None, percent: Decimal | None) -> str:
        if value is None:
            return "Not available"
        pct = f" ({percent:+.2f}%)" if percent is not None else ""
        return f"{value:+.4f} USDC{pct}"

    def _base_asset(self, symbol: str) -> str:
        for quote in ("USDC", "USDT", "FDUSD", "BTC", "ETH", "BNB"):
            if symbol.endswith(quote):
                return symbol[: -len(quote)]
        return symbol

    def _rebalancing_basket(self, connection: sqlite3.Connection, run_id: int) -> str:
        if not self._table_exists(connection, "rebalancing_bot_assets"):
            return ""
        rows = connection.execute(
            """
            select asset, target_weight_pct from rebalancing_bot_assets
            where run_id = ? and status != 'EXCLUDED'
            order by cast(target_weight_pct as real) desc
            """,
            (run_id,),
        ).fetchall()
        return ", ".join(f"{row['asset']} {self._percent(row['target_weight_pct'])}" for row in rows)

    def _rebalancing_registration_suggestion(
        self,
        connection: sqlite3.Connection,
        run_id: int,
        investment: object,
        threshold: object,
    ) -> dict[str, object]:
        if not self._table_exists(connection, "rebalancing_bot_assets"):
            return {"available": False}
        rows = connection.execute(
            """
            select asset, target_weight_pct from rebalancing_bot_assets
            where run_id = ? and status != 'EXCLUDED'
            order by cast(target_weight_pct as real) desc
            """,
            (run_id,),
        ).fetchall()
        assets = tuple(str(row["asset"] or "").upper() for row in rows if row["asset"])
        weights = tuple(self._number(row["target_weight_pct"]) for row in rows if row["asset"])
        prices = tuple(self._market_price_for_run(connection, run_id, f"{asset}USDC") for asset in assets)
        entry_prices = ", ".join(self._number(price) for price in prices) if prices and all(price is not None for price in prices) else ""
        return {
            "available": bool(assets),
            "name": "Core Rebalancing Basket",
            "assets": ", ".join(assets),
            "targetWeights": ", ".join(weights),
            "entryPrices": entry_prices,
            "investment": self._number(investment),
            "threshold": self._number(threshold),
            "sourceRun": str(run_id),
        }


    def _history(self, connection: sqlite3.Connection) -> tuple[dict[str, str], ...]:
        rows = connection.execute(
            """
            select r.id, r.started_at, r.status, r.summary, mr.status as data_status,
                   sd.decision_type, sd.summary as decision_summary
            from runs r
            left join market_research_reports mr on mr.run_id = r.id
            left join strategy_decisions sd on sd.run_id = r.id
            order by r.id desc
            limit 30
            """
        ).fetchall()
        return tuple(
            {
                "runId": str(row["id"]),
                "startedAt": self._local_started_at(row["started_at"]),
                "status": str(row["status"]),
                "dataMode": "MOCK" if row["data_status"] == "MOCK" else "REAL",
                "decision": str(row["decision_type"] or "UNKNOWN"),
                "summary": str(row["decision_summary"] or row["summary"] or ""),
                # Every run wrote a report, but only the newest one could be
                # opened - from the Action Plan. Run History listed the rest
                # with no way to read any of them.
                "reportPath": str(self._report_path(row) or ""),
            }
            for row in rows
        )

    def _report_path(self, row: sqlite3.Row) -> Path | None:
        summary = str(row["summary"] or "")
        match = re.search(r"Report written to (.+)$", summary)
        if match:
            path = Path(match.group(1).strip())
            if path.exists():
                return path
        candidates = sorted(self.reports_dir.glob(f"*_run-{row['id']}.md"))
        return candidates[-1] if candidates else None

    def _range(self, low: object, high: object) -> str:
        left = "" if low in (None, "") else str(low)
        right = "" if high in (None, "") else str(high)
        return " - ".join(part for part in (left, right) if part)

    # Schema introspection is delegated to trading_agent.storage, which owns the
    # schema these reads depend on. Kept as thin methods so the existing call
    # sites and their tests stay unchanged.
    def _table_exists(self, connection: sqlite3.Connection, table: str) -> bool:
        return table_exists(connection, table)

    def _columns(self, connection: sqlite3.Connection, table: str) -> set[str]:
        return table_columns(connection, table)

    def _column_expr(self, columns: set[str], column: str) -> str:
        return column_or_null(columns, column)

    def _money(self, value: object) -> str:
        try:
            return f"{float(value):,.2f} USDC"
        except (TypeError, ValueError):
            return "0.00 USDC"

    def _percent(self, value: object) -> str:
        try:
            return f"{float(value):.2f}%"
        except (TypeError, ValueError):
            return "0.00%"
