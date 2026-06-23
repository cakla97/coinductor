from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sqlite3

from .models import ActiveStrategiesReport, AiCommentary, AiDecisionMemory, Balance, CapitalSourcingPlan, ClosedTradeMemory, EarnRedeemPlan, ExecutionChecklistItem, GridRecommendation, LivePositionCycle, LivePositionSummary, LivePreviewReport, MarketResearchReport, MarketSnapshot, NextRunRecommendation, OcoProtectionPreviewReport, OcoStatusReport, PaperExecutionReport, PortfolioAnalysis, RecommendedAction, ResearchBundle, ResearchStatus, RiskDecision, ShadowEvaluation, StrategyDecision, TestnetExecutionReport, TestnetPositionCycle, TestnetPositionSummary, TradeProposal, TradingBankrollReport


class Storage:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self._migrate()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            create table if not exists runs (
                id integer primary key autoincrement,
                started_at text not null default current_timestamp,
                mode text not null,
                status text not null,
                summary text
            );
            create table if not exists balances (
                run_id integer,
                asset text,
                spot_free text,
                spot_locked text,
                flexible_amount text,
                locked_amount text
            );
            create table if not exists portfolio_valuations (
                run_id integer,
                asset text,
                role text,
                price_usdt text,
                spot_value_usdt text,
                flexible_value_usdt text,
                locked_value_usdt text,
                total_value_usdt text,
                allocation_pct text,
                target_pct text,
                gap_pct text,
                rebalance_action text
            );
            create table if not exists portfolio_summaries (
                run_id integer,
                total_value_usdt text,
                spot_value_usdt text,
                flexible_value_usdt text,
                locked_value_usdt text,
                liquid_value_usdt text,
                locked_pct text,
                unpriced_assets text,
                ignored_internal_assets text,
                rebalance_summary text,
                liquidity_summary text
            );
            create table if not exists market_snapshots (
                run_id integer,
                symbol text,
                price text,
                rsi14 text,
                ema20 text,
                ema50 text,
                ema200 text,
                atr14 text,
                trend_regime text
            );
            create table if not exists market_research_reports (
                run_id integer,
                enabled integer,
                status text,
                summary text,
                errors text,
                quote_asset text,
                symbols_analyzed integer,
                advancing integer,
                declining integer,
                unchanged integer,
                advance_pct text,
                median_change_24h_pct text
            );
            create table if not exists market_research_symbols (
                run_id integer,
                symbol text,
                change_24h_pct text,
                return_7d_pct text,
                return_30d_pct text,
                quote_volume_24h text,
                trades_24h integer,
                range_24h_pct text,
                atr_pct text,
                price_vs_ema200_pct text,
                relative_strength_vs_btc_24h_pct text,
                volume_trend text,
                trend_regime text
            );
            create table if not exists ai_proposals (
                run_id integer,
                symbol text,
                action text,
                confidence text,
                quote_amount_usdt text,
                reason text
            );
            create table if not exists shadow_signals (
                run_id integer primary key,
                symbol text,
                action text,
                confidence text,
                entry_price text,
                horizon_hours integer,
                status text,
                universe_entry_prices text,
                proposal_reason text,
                evaluated_run_id integer,
                evaluation_price text,
                elapsed_hours text,
                symbol_return_pct text,
                best_universe_symbol text,
                best_universe_return_pct text,
                verdict text,
                score text,
                price_source text
            );
            create table if not exists risk_decisions (
                run_id integer,
                approved integer,
                reason text,
                adjusted_quote_amount_usdt text
            );
            create table if not exists paper_orders (
                run_id integer,
                intent_id text,
                symbol text,
                side text,
                quote_amount_usdt text,
                simulated_price text,
                simulated_quantity text,
                fee_usdt text,
                slippage_usdt text,
                stop_loss_price text,
                take_profit_price text,
                status text,
                reason text
            );
            create table if not exists testnet_orders (
                run_id integer,
                intent_id text,
                symbol text,
                side text,
                quote_amount_usdt text,
                client_order_id text,
                submitted integer,
                status text,
                executed_quantity text,
                cumulative_quote_qty text,
                order_id text,
                queried_status text,
                validation_summary text,
                message text
            );
            create table if not exists live_orders (
                run_id integer,
                intent_id text,
                symbol text,
                side text,
                order_type text,
                quote_amount_usdt text,
                quote_asset text,
                status text,
                submitted integer,
                order_id text,
                executed_quantity text,
                cumulative_quote_qty text,
                validation_summary text,
                message text
            );
            create table if not exists oco_protection_orders (
                run_id integer,
                intent_id text,
                symbol text,
                side text,
                status text,
                quantity text,
                adjusted_quantity text,
                available_base text,
                take_profit_price text,
                stop_loss_stop_price text,
                estimated_take_profit_quote text,
                estimated_stop_quote text,
                submitted integer,
                order_list_id text,
                confirmation_required text,
                reason text,
                message text
            );
            create table if not exists oco_status_checks (
                run_id integer,
                intent_id text,
                symbol text,
                order_list_id text,
                list_order_status text,
                list_status_type text,
                filled_order_id text,
                filled_quantity text,
                filled_quote text,
                reconciled integer,
                message text
            );
            create table if not exists grid_recommendations (
                run_id integer,
                recommended integer,
                symbol text,
                reason text,
                range_low text,
                range_high text,
                grid_count integer,
                investment_usdt text,
                stop_loss_price text,
                take_profit_price text
            );
            create table if not exists strategy_decisions (
                run_id integer,
                decision_type text,
                priority text,
                summary text,
                rebalancing_note text
            );
            create table if not exists capital_sourcing_plans (
                run_id integer,
                plan_type text,
                needed_usdt text,
                available_usdt text,
                missing_usdt text,
                recommended integer,
                summary text
            );
            create table if not exists capital_sourcing_items (
                run_id integer,
                plan_type text,
                asset text,
                action text,
                value_usdt text,
                source_pct_of_asset text,
                remaining_value_usdt text,
                remaining_pct_of_asset text,
                reason text
            );
            create table if not exists trading_bankroll_reports (
                run_id integer,
                enabled integer,
                quote_asset text,
                initial_seed text,
                spot_free text,
                flexible_amount text,
                total_quote text,
                realized_pnl text,
                profit_available text,
                seed_capital_at_risk text,
                required_amount text,
                preferred_source text,
                max_profit_trade_amount text,
                flexible_draw_needed text,
                summary text
            );
            create table if not exists earn_redeem_plans (
                run_id integer,
                enabled integer,
                asset text,
                amount text,
                status text,
                product_id text,
                redeem_type text,
                can_redeem integer,
                submitted integer,
                confirmation_required text,
                message text
            );
            create table if not exists next_run_recommendations (
                run_id integer,
                run_again_in_hours integer,
                urgency text,
                reason text,
                triggers text
            );
            create table if not exists recommended_actions (
                run_id integer,
                priority text,
                action text,
                reason text
            );
            create table if not exists execution_checklist_items (
                run_id integer,
                priority text,
                step text,
                detail text
            );
            create table if not exists ai_commentaries (
                run_id integer,
                enabled integer,
                summary text,
                risks text,
                watchlist text,
                raw_response text
            );
            create table if not exists research_notes (
                run_id integer,
                source text,
                title text,
                content text
            );
            create table if not exists research_statuses (
                run_id integer,
                enabled integer,
                notes_count integer,
                is_fresh integer,
                latest_note_age_hours text,
                request_path text,
                summary text
            );
            create table if not exists active_grid_evaluations (
                run_id integer,
                name text,
                symbol text,
                range_low text,
                range_high text,
                investment_usdt text,
                current_price text,
                state text,
                distance_to_lower_pct text,
                distance_to_upper_pct text,
                recommendation text
            );
            """
        )
        self._ensure_column("portfolio_summaries", "unpriced_assets", "text")
        self._ensure_column("portfolio_summaries", "ignored_internal_assets", "text")
        self._ensure_column("portfolio_valuations", "role", "text")
        self._ensure_column("paper_orders", "intent_id", "text")
        self._ensure_column("testnet_orders", "queried_status", "text")
        self._ensure_column("testnet_orders", "validation_summary", "text")
        self._ensure_column("live_orders", "executed_quantity", "text")
        self._ensure_column("live_orders", "cumulative_quote_qty", "text")
        self._ensure_column("capital_sourcing_items", "source_pct_of_asset", "text")
        self._ensure_column("capital_sourcing_items", "remaining_value_usdt", "text")
        self._ensure_column("capital_sourcing_items", "remaining_pct_of_asset", "text")
        self._ensure_column("shadow_signals", "price_source", "text")
        self.connection.commit()

    def _ensure_column(self, table: str, column: str, definition: str) -> None:
        columns = {row["name"] for row in self.connection.execute(f"pragma table_info({table})")}
        if column not in columns:
            self.connection.execute(f"alter table {table} add column {column} {definition}")

    def start_run(self, mode: str) -> int:
        cursor = self.connection.execute("insert into runs(mode, status) values (?, ?)", (mode, "RUNNING"))
        self.connection.commit()
        return int(cursor.lastrowid)

    def finish_run(self, run_id: int, status: str, summary: str) -> None:
        self.connection.execute("update runs set status = ?, summary = ? where id = ?", (status, summary, run_id))
        self.connection.commit()

    def count_trades_today(self) -> int:
        row = self.connection.execute(
            """
            select count(distinct live.intent_id) as trade_count
            from live_orders live
            join runs on runs.id = live.run_id
            where live.side = 'BUY'
              and live.submitted = 1
              and live.status = 'FILLED'
              and date(runs.started_at) = date('now')
            """
        ).fetchone()
        return int(row["trade_count"] or 0)

    def save_balances(self, run_id: int, balances: list[Balance]) -> None:
        self.connection.executemany(
            "insert into balances values (?, ?, ?, ?, ?, ?)",
            [(run_id, b.asset, str(b.spot_free), str(b.spot_locked), str(b.flexible_amount), str(b.locked_amount)) for b in balances],
        )
        self.connection.commit()

    def save_portfolio_analysis(self, run_id: int, analysis: PortfolioAnalysis) -> None:
        self.connection.execute(
            """
            insert into portfolio_summaries (
                run_id,
                total_value_usdt,
                spot_value_usdt,
                flexible_value_usdt,
                locked_value_usdt,
                liquid_value_usdt,
                locked_pct,
                unpriced_assets,
                ignored_internal_assets,
                rebalance_summary,
                liquidity_summary
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                str(analysis.total_value_usdt),
                str(analysis.spot_value_usdt),
                str(analysis.flexible_value_usdt),
                str(analysis.locked_value_usdt),
                str(analysis.liquid_value_usdt),
                str(analysis.locked_pct),
                ",".join(analysis.unpriced_assets),
                ",".join(analysis.ignored_internal_assets),
                analysis.rebalance_summary,
                analysis.liquidity_summary,
            ),
        )
        self.connection.executemany(
            """
            insert into portfolio_valuations (
                run_id,
                asset,
                role,
                price_usdt,
                spot_value_usdt,
                flexible_value_usdt,
                locked_value_usdt,
                total_value_usdt,
                allocation_pct,
                target_pct,
                gap_pct,
                rebalance_action
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    asset.asset,
                    asset.role,
                    str(asset.price_usdt),
                    str(asset.spot_value_usdt),
                    str(asset.flexible_value_usdt),
                    str(asset.locked_value_usdt),
                    str(asset.total_value_usdt),
                    str(asset.allocation_pct),
                    str(asset.target_pct) if asset.target_pct is not None else None,
                    str(asset.gap_pct) if asset.gap_pct is not None else None,
                    asset.rebalance_action,
                )
                for asset in analysis.assets
            ],
        )
        self.connection.commit()

    def save_market_snapshots(self, run_id: int, snapshots: list[MarketSnapshot]) -> None:
        self.connection.executemany(
            "insert into market_snapshots values (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (run_id, s.symbol, str(s.price), str(s.rsi14), str(s.ema20), str(s.ema50), str(s.ema200), str(s.atr14), s.trend_regime)
                for s in snapshots
            ],
        )
        self.connection.commit()

    def save_market_research(self, run_id: int, report: MarketResearchReport) -> None:
        breadth = report.breadth
        self.connection.execute(
            """
            insert into market_research_reports (
                run_id, enabled, status, summary, errors, quote_asset, symbols_analyzed,
                advancing, declining, unchanged, advance_pct, median_change_24h_pct
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                int(report.enabled),
                report.status,
                report.summary,
                "\n".join(report.errors),
                breadth.quote_asset if breadth is not None else None,
                breadth.symbols_analyzed if breadth is not None else 0,
                breadth.advancing if breadth is not None else 0,
                breadth.declining if breadth is not None else 0,
                breadth.unchanged if breadth is not None else 0,
                str(breadth.advance_pct) if breadth is not None else None,
                str(breadth.median_change_24h_pct) if breadth is not None else None,
            ),
        )
        self.connection.executemany(
            """
            insert into market_research_symbols (
                run_id, symbol, change_24h_pct, return_7d_pct, return_30d_pct,
                quote_volume_24h, trades_24h, range_24h_pct, atr_pct,
                price_vs_ema200_pct, relative_strength_vs_btc_24h_pct,
                volume_trend, trend_regime
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item.symbol,
                    str(item.change_24h_pct),
                    str(item.return_7d_pct) if item.return_7d_pct is not None else None,
                    str(item.return_30d_pct) if item.return_30d_pct is not None else None,
                    str(item.quote_volume_24h),
                    item.trades_24h,
                    str(item.range_24h_pct),
                    str(item.atr_pct),
                    str(item.price_vs_ema200_pct),
                    str(item.relative_strength_vs_btc_24h_pct)
                    if item.relative_strength_vs_btc_24h_pct is not None
                    else None,
                    item.volume_trend,
                    item.trend_regime,
                )
                for item in report.symbols
            ],
        )
        self.connection.commit()

    def save_proposal(self, run_id: int, proposal: TradeProposal) -> None:
        self.connection.execute(
            "insert into ai_proposals values (?, ?, ?, ?, ?, ?)",
            (run_id, proposal.symbol, proposal.action, str(proposal.confidence), str(proposal.quote_amount_usdt), proposal.reason),
        )
        self.connection.commit()

    def save_shadow_signal(
        self,
        run_id: int,
        proposal: TradeProposal,
        entry_price: Decimal,
        horizon_hours: int,
        universe_entry_prices: str,
    ) -> bool:
        cursor = self.connection.execute(
            """
            insert or ignore into shadow_signals (
                run_id, symbol, action, confidence, entry_price, horizon_hours, status,
                universe_entry_prices, proposal_reason
            ) values (?, ?, ?, ?, ?, ?, 'PENDING', ?, ?)
            """,
            (
                run_id,
                proposal.symbol,
                proposal.action,
                str(proposal.confidence),
                str(entry_price),
                horizon_hours,
                universe_entry_prices,
                proposal.reason,
            ),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    def get_shadow_signal_cooldown(
        self,
        current_run_id: int,
        min_interval_hours: int,
    ) -> dict[str, object] | None:
        row = self.connection.execute(
            """
            select
                signal.run_id,
                signal.symbol,
                signal.action,
                signal.status,
                (julianday(current_run.started_at) - julianday(signal_run.started_at)) * 24
                    as elapsed_hours
            from shadow_signals signal
            join runs signal_run on signal_run.id = signal.run_id
            join runs current_run on current_run.id = ?
            where signal.run_id != ?
              and signal_run.status = 'OK'
            order by signal_run.started_at desc, signal.run_id desc
            limit 1
            """,
            (current_run_id, current_run_id),
        ).fetchone()
        if row is None:
            return None
        elapsed = Decimal(str(row["elapsed_hours"]))
        if elapsed >= Decimal(min_interval_hours):
            return None
        return {
            "run_id": int(row["run_id"]),
            "symbol": str(row["symbol"]),
            "action": str(row["action"]),
            "status": str(row["status"]),
            "elapsed_hours": elapsed,
            "remaining_hours": max(Decimal("0"), Decimal(min_interval_hours) - elapsed),
        }

    def get_due_shadow_signals(self, current_run_id: int) -> list[sqlite3.Row]:
        return self.connection.execute(
            """
            select
                signal.*,
                (julianday(current_run.started_at) - julianday(signal_run.started_at)) * 24
                    as evaluation_delay_hours,
                (cast(strftime('%s', signal_run.started_at) as integer) + signal.horizon_hours * 3600) * 1000
                    as target_timestamp_ms
            from shadow_signals signal
            join runs signal_run on signal_run.id = signal.run_id
            join runs current_run on current_run.id = ?
            where signal.status = 'PENDING'
              and signal_run.status = 'OK'
              and signal.run_id != ?
              and (julianday(current_run.started_at) - julianday(signal_run.started_at)) * 24 >= signal.horizon_hours
            order by signal.run_id
            """,
            (current_run_id, current_run_id),
        ).fetchall()

    def complete_shadow_signal(self, evaluation: ShadowEvaluation) -> None:
        self.connection.execute(
            """
            update shadow_signals
            set status = 'EVALUATED',
                evaluated_run_id = ?,
                evaluation_price = ?,
                elapsed_hours = ?,
                symbol_return_pct = ?,
                best_universe_symbol = ?,
                best_universe_return_pct = ?,
                verdict = ?,
                score = ?,
                price_source = ?
            where run_id = ? and status = 'PENDING'
            """,
            (
                evaluation.evaluated_run_id,
                str(evaluation.evaluation_price),
                str(evaluation.elapsed_hours),
                str(evaluation.symbol_return_pct),
                evaluation.best_universe_symbol,
                str(evaluation.best_universe_return_pct),
                evaluation.verdict,
                evaluation.score,
                evaluation.price_source,
                evaluation.signal_run_id,
            ),
        )
        self.connection.commit()

    def get_shadow_evaluation_counts(self) -> dict[str, int]:
        row = self.connection.execute(
            """
            select
                sum(case when signal.status = 'PENDING' then 1 else 0 end) as pending,
                sum(case when signal.status = 'EVALUATED' then 1 else 0 end) as completed,
                sum(case when signal.score = 'CORRECT' then 1 else 0 end) as correct,
                sum(case when signal.score = 'WRONG' then 1 else 0 end) as wrong,
                sum(case when signal.score = 'NEUTRAL' then 1 else 0 end) as neutral
            from shadow_signals signal
            join runs on runs.id = signal.run_id
            where runs.status in ('RUNNING', 'OK')
            """
        ).fetchone()
        return {
            "pending": int(row["pending"] or 0),
            "completed": int(row["completed"] or 0),
            "correct": int(row["correct"] or 0),
            "wrong": int(row["wrong"] or 0),
            "neutral": int(row["neutral"] or 0),
        }

    def save_risk_decision(self, run_id: int, decision: RiskDecision) -> None:
        self.connection.execute(
            "insert into risk_decisions values (?, ?, ?, ?)",
            (run_id, int(decision.approved), decision.reason, str(decision.adjusted_quote_amount_usdt)),
        )
        self.connection.commit()

    def save_paper_execution(self, run_id: int, paper: PaperExecutionReport) -> None:
        self.connection.executemany(
            """
            insert into paper_orders (
                run_id,
                intent_id,
                symbol,
                side,
                quote_amount_usdt,
                simulated_price,
                simulated_quantity,
                fee_usdt,
                slippage_usdt,
                stop_loss_price,
                take_profit_price,
                status,
                reason
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    order.intent_id,
                    order.symbol,
                    order.side,
                    str(order.quote_amount_usdt),
                    str(order.simulated_price),
                    str(order.simulated_quantity),
                    str(order.fee_usdt),
                    str(order.slippage_usdt),
                    str(order.stop_loss_price),
                    str(order.take_profit_price),
                    order.status,
                    order.reason,
                )
                for order in paper.orders
            ],
        )
        self.connection.commit()

    def get_existing_paper_intents(self) -> set[str]:
        columns = {row["name"] for row in self.connection.execute("pragma table_info(paper_orders)")}
        if "intent_id" not in columns:
            return set()
        return {row["intent_id"] for row in self.connection.execute("select intent_id from paper_orders where intent_id is not null")}

    def save_testnet_execution(self, run_id: int, report: TestnetExecutionReport) -> None:
        self.connection.executemany(
            """
            insert into testnet_orders (
                run_id,
                intent_id,
                symbol,
                side,
                quote_amount_usdt,
                client_order_id,
                submitted,
                status,
                executed_quantity,
                cumulative_quote_qty,
                order_id,
                queried_status,
                validation_summary,
                message
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    order.intent_id,
                    order.symbol,
                    order.side,
                    str(order.quote_amount_usdt),
                    order.client_order_id,
                    int(order.submitted),
                    order.status,
                    str(order.executed_quantity),
                    str(order.cumulative_quote_qty),
                    order.order_id,
                    order.queried_status,
                    order.validation_summary,
                    order.message,
                )
                for order in report.orders
            ],
        )
        self.connection.commit()

    def get_existing_testnet_intents(self) -> set[str]:
        return {
            row["intent_id"]
            for row in self.connection.execute(
                "select intent_id from testnet_orders where intent_id is not null and submitted = 1 and status not in ('ERROR', 'SKIPPED')"
            )
        }

    def get_existing_live_intents(self) -> set[str]:
        return {
            row["intent_id"]
            for row in self.connection.execute(
                "select intent_id from live_orders where intent_id is not null and submitted = 1 and status not in ('SUBMIT_ERROR', 'SUBMIT_SKIPPED')"
            )
        }

    def get_existing_oco_intents(self) -> set[str]:
        return {
            row["intent_id"]
            for row in self.connection.execute(
                "select intent_id from oco_protection_orders where intent_id is not null and submitted = 1 and status not in ('SUBMIT_ERROR', 'SUBMIT_SKIPPED')"
            )
        }

    def get_submitted_oco_records(self) -> list[dict[str, str]]:
        rows = self.connection.execute(
            """
            select intent_id, symbol, order_list_id
            from oco_protection_orders
            where submitted = 1
              and order_list_id is not null
              and order_list_id != ''
            order by run_id desc
            """
        ).fetchall()
        seen: set[str] = set()
        records: list[dict[str, str]] = []
        for row in rows:
            intent_id = str(row["intent_id"])
            if intent_id in seen:
                continue
            seen.add(intent_id)
            records.append(
                {
                    "intent_id": intent_id,
                    "symbol": str(row["symbol"]),
                    "order_list_id": str(row["order_list_id"]),
                }
            )
        return records

    def has_live_sell_for_intent(self, sell_intent_id: str) -> bool:
        row = self.connection.execute(
            """
            select 1
            from live_orders
            where intent_id = ?
              and side = 'SELL'
              and submitted = 1
              and status = 'FILLED'
            limit 1
            """,
            (sell_intent_id,),
        ).fetchone()
        return row is not None

    def save_live_preview(self, run_id: int, report: LivePreviewReport) -> None:
        self.connection.executemany(
            """
            insert into live_orders (
                run_id,
                intent_id,
                symbol,
                side,
                order_type,
                quote_amount_usdt,
                quote_asset,
                status,
                submitted,
                order_id,
                executed_quantity,
                cumulative_quote_qty,
                validation_summary,
                message
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    order.intent_id,
                    order.symbol,
                    order.side,
                    order.order_type,
                    str(order.quote_amount_usdt),
                    order.quote_asset,
                    order.status,
                    int(order.submitted),
                    order.order_id,
                    str(order.executed_quantity),
                    str(order.cumulative_quote_qty),
                    order.validation_summary,
                    order.message,
                )
                for order in report.orders
            ],
        )
        self.connection.commit()

    def save_oco_status_report(self, run_id: int, report: OcoStatusReport) -> None:
        self.connection.executemany(
            """
            insert into oco_status_checks (
                run_id,
                intent_id,
                symbol,
                order_list_id,
                list_order_status,
                list_status_type,
                filled_order_id,
                filled_quantity,
                filled_quote,
                reconciled,
                message
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item.intent_id,
                    item.symbol,
                    item.order_list_id,
                    item.list_order_status,
                    item.list_status_type,
                    item.filled_order_id,
                    str(item.filled_quantity),
                    str(item.filled_quote),
                    int(item.reconciled),
                    item.message,
                )
                for item in report.items
            ],
        )
        self.connection.commit()

    def record_live_sell_from_oco(
        self,
        run_id: int,
        intent_id: str,
        symbol: str,
        order_id: str,
        executed_quantity: Decimal,
        cumulative_quote_qty: Decimal,
        message: str,
    ) -> None:
        self.connection.execute(
            """
            insert into live_orders (
                run_id,
                intent_id,
                symbol,
                side,
                order_type,
                quote_amount_usdt,
                quote_asset,
                status,
                submitted,
                order_id,
                executed_quantity,
                cumulative_quote_qty,
                validation_summary,
                message
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                intent_id,
                symbol,
                "SELL",
                "OCO",
                "0",
                self._quote_asset(symbol),
                "FILLED",
                1,
                order_id,
                str(executed_quantity),
                str(cumulative_quote_qty),
                "Recorded from filled Binance OCO protection order.",
                message,
            ),
        )
        self.connection.commit()

    def save_oco_protection_preview(self, run_id: int, report: OcoProtectionPreviewReport) -> None:
        self.connection.executemany(
            """
            insert into oco_protection_orders (
                run_id,
                intent_id,
                symbol,
                side,
                status,
                quantity,
                adjusted_quantity,
                available_base,
                take_profit_price,
                stop_loss_stop_price,
                estimated_take_profit_quote,
                estimated_stop_quote,
                submitted,
                order_list_id,
                confirmation_required,
                reason,
                message
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    item.intent_id,
                    item.symbol,
                    item.side,
                    item.status,
                    str(item.quantity),
                    str(item.adjusted_quantity),
                    str(item.available_base),
                    str(item.take_profit_price),
                    str(item.stop_loss_stop_price),
                    str(item.estimated_take_profit_quote),
                    str(item.estimated_stop_quote),
                    int(item.submitted),
                    item.order_list_id,
                    item.confirmation_required,
                    item.reason,
                    item.message,
                )
                for item in report.items
            ],
        )
        self.connection.commit()

    def get_latest_filled_testnet_buy(self, symbol: str) -> dict[str, str] | None:
        row = self.connection.execute(
            """
            select
                run_id,
                intent_id,
                symbol,
                executed_quantity,
                cumulative_quote_qty,
                order_id,
                client_order_id
            from testnet_orders
            where symbol = ?
              and side = 'BUY'
              and submitted = 1
              and status = 'FILLED'
              and cast(executed_quantity as real) > 0
              and not exists (
                  select 1
                  from testnet_orders sell
                  where sell.intent_id = 'sell-' || testnet_orders.intent_id
                    and sell.side = 'SELL'
                    and sell.submitted = 1
                    and sell.status = 'FILLED'
              )
            order by run_id desc
            limit 1
            """,
            (symbol.upper(),),
        ).fetchone()
        if row is None:
            return None
        return {key: str(row[key]) for key in row.keys()}

    def get_testnet_position_summary(self) -> TestnetPositionSummary:
        buys = self.connection.execute(
            """
            select intent_id, symbol, executed_quantity, cumulative_quote_qty, order_id
            from testnet_orders
            where side = 'BUY'
              and submitted = 1
              and status = 'FILLED'
              and cast(executed_quantity as real) > 0
            order by run_id desc
            limit 50
            """
        ).fetchall()
        open_positions: list[TestnetPositionCycle] = []
        closed_positions: list[TestnetPositionCycle] = []
        total_pnl = Decimal("0")
        for buy in buys:
            sell = self.connection.execute(
                """
                select executed_quantity, cumulative_quote_qty, order_id
                from testnet_orders
                where intent_id = ?
                  and side = 'SELL'
                  and submitted = 1
                  and status = 'FILLED'
                order by run_id desc
                limit 1
                """,
                (f"sell-{buy['intent_id']}",),
            ).fetchone()
            buy_quote = Decimal(str(buy["cumulative_quote_qty"]))
            quantity = Decimal(str(buy["executed_quantity"]))
            if sell is None:
                open_positions.append(
                    TestnetPositionCycle(
                        symbol=str(buy["symbol"]),
                        buy_order_id=str(buy["order_id"]),
                        sell_order_id=None,
                        buy_quote_usdt=buy_quote,
                        sell_quote_usdt=None,
                        quantity=quantity,
                        status="OPEN",
                        pnl_usdt=None,
                    )
                )
                continue
            sell_quote = Decimal(str(sell["cumulative_quote_qty"]))
            pnl = sell_quote - buy_quote
            total_pnl += pnl
            closed_positions.append(
                TestnetPositionCycle(
                    symbol=str(buy["symbol"]),
                    buy_order_id=str(buy["order_id"]),
                    sell_order_id=str(sell["order_id"]),
                    buy_quote_usdt=buy_quote,
                    sell_quote_usdt=sell_quote,
                    quantity=quantity,
                    status="CLOSED",
                    pnl_usdt=pnl,
                )
            )
        summary = (
            f"{len(open_positions)} open testnet position(s), {len(closed_positions)} closed cycle(s), "
            f"realized PnL {total_pnl} USDT."
        )
        return TestnetPositionSummary(
            enabled=True,
            open_positions=tuple(open_positions),
            closed_positions=tuple(closed_positions),
            total_realized_pnl_usdt=total_pnl,
            summary=summary,
        )

    def get_live_position_summary(self, snapshots: list[MarketSnapshot], config: dict) -> LivePositionSummary:
        buys = self.connection.execute(
            """
            select intent_id, symbol, executed_quantity, cumulative_quote_qty, order_id
            from live_orders
            where side = 'BUY'
              and submitted = 1
              and status = 'FILLED'
              and cast(executed_quantity as real) > 0
            order by run_id desc
            limit 50
            """
        ).fetchall()
        price_by_symbol = {snapshot.symbol: snapshot.price for snapshot in snapshots}
        open_positions: list[LivePositionCycle] = []
        closed_positions: list[LivePositionCycle] = []
        total_realized = Decimal("0")
        for buy in buys:
            sell = self.connection.execute(
                """
                select executed_quantity, cumulative_quote_qty, order_id
                from live_orders
                where intent_id = ?
                  and side = 'SELL'
                  and submitted = 1
                  and status = 'FILLED'
                order by run_id desc
                limit 1
                """,
                (f"sell-{buy['intent_id']}",),
            ).fetchone()
            symbol = str(buy["symbol"])
            quantity = Decimal(str(buy["executed_quantity"] or "0"))
            buy_quote = Decimal(str(buy["cumulative_quote_qty"] or "0"))
            entry_price = self._safe_div(buy_quote, quantity)
            stop_loss = entry_price * (Decimal("1") - Decimal(str(config.get("orders", {}).get("default_stop_loss_pct", "0"))) / Decimal("100"))
            take_profit = entry_price * (Decimal("1") + Decimal(str(config.get("orders", {}).get("default_take_profit_pct", "0"))) / Decimal("100"))
            if sell is not None:
                sell_quantity = Decimal(str(sell["executed_quantity"] or "0"))
                sell_quote = Decimal(str(sell["cumulative_quote_qty"] or "0"))
                closed_quantity = min(quantity, sell_quantity)
                allocated_buy_quote = buy_quote * self._safe_div(closed_quantity, quantity)
                pnl = sell_quote - allocated_buy_quote
                residual_quantity = max(Decimal("0"), quantity - closed_quantity)
                total_realized += pnl
                closed_positions.append(
                    LivePositionCycle(
                        intent_id=str(buy["intent_id"]),
                        symbol=symbol,
                        buy_order_id=str(buy["order_id"]),
                        sell_order_id=str(sell["order_id"]),
                        buy_quote=allocated_buy_quote,
                        sell_quote=sell_quote,
                        quantity=closed_quantity,
                        entry_price=entry_price,
                        current_price=None,
                        current_value=None,
                        pnl_quote=pnl,
                        pnl_pct=self._safe_pct(pnl, allocated_buy_quote),
                        stop_loss_price=stop_loss,
                        take_profit_price=take_profit,
                        status="CLOSED",
                        exit_preview_status="CLOSED",
                        exit_preview_reason=f"Position strategy cycle is closed; residual base dust is {residual_quantity}.",
                    )
                )
                continue

            current_price = price_by_symbol.get(symbol)
            current_value = quantity * current_price if current_price is not None else None
            pnl = current_value - buy_quote if current_value is not None else None
            pnl_pct = self._safe_pct(pnl, buy_quote) if pnl is not None else None
            exit_status, exit_reason = self._exit_preview(current_price, stop_loss, take_profit)
            open_positions.append(
                LivePositionCycle(
                    intent_id=str(buy["intent_id"]),
                    symbol=symbol,
                    buy_order_id=str(buy["order_id"]),
                    sell_order_id=None,
                    buy_quote=buy_quote,
                    sell_quote=None,
                    quantity=quantity,
                    entry_price=entry_price,
                    current_price=current_price,
                    current_value=current_value,
                    pnl_quote=pnl,
                    pnl_pct=pnl_pct,
                    stop_loss_price=stop_loss,
                    take_profit_price=take_profit,
                    status="OPEN",
                    exit_preview_status=exit_status,
                    exit_preview_reason=exit_reason,
                )
            )
        summary = (
            f"{len(open_positions)} open live position(s), {len(closed_positions)} closed live cycle(s), "
            f"realized PnL {total_realized} quote units."
        )
        return LivePositionSummary(
            enabled=True,
            open_positions=tuple(open_positions),
            closed_positions=tuple(closed_positions),
            total_realized_pnl_quote=total_realized,
            summary=summary,
        )

    def get_ai_decision_memory(self, config: dict) -> AiDecisionMemory:
        memory_config = config.get("ai_memory", {})
        enabled = bool(memory_config.get("enabled", True))
        max_cycles = max(1, min(int(memory_config.get("max_closed_cycles", 10)), 50))
        if not enabled:
            return AiDecisionMemory(False, 0, 0, 0, Decimal("0"), (), "AI decision memory is disabled.")

        buys = self.connection.execute(
            """
            select run_id, intent_id, symbol, executed_quantity, cumulative_quote_qty
            from live_orders
            where side = 'BUY'
              and submitted = 1
              and status = 'FILLED'
              and cast(executed_quantity as real) > 0
            order by run_id desc
            limit 50
            """
        ).fetchall()
        cycles: list[ClosedTradeMemory] = []
        for buy in buys:
            sell = self.connection.execute(
                """
                select executed_quantity, cumulative_quote_qty
                from live_orders
                where intent_id = ?
                  and side = 'SELL'
                  and submitted = 1
                  and status = 'FILLED'
                order by run_id desc
                limit 1
                """,
                (f"sell-{buy['intent_id']}",),
            ).fetchone()
            if sell is None:
                continue

            quantity = Decimal(str(buy["executed_quantity"] or "0"))
            buy_quote = Decimal(str(buy["cumulative_quote_qty"] or "0"))
            sell_quantity = Decimal(str(sell["executed_quantity"] or "0"))
            sell_quote = Decimal(str(sell["cumulative_quote_qty"] or "0"))
            closed_quantity = min(quantity, sell_quantity)
            if quantity <= 0 or closed_quantity <= 0:
                continue
            allocated_buy_quote = buy_quote * self._safe_div(closed_quantity, quantity)
            pnl = sell_quote - allocated_buy_quote
            entry_price = self._safe_div(buy_quote, quantity)
            exit_price = self._safe_div(sell_quote, closed_quantity)
            snapshot = self.connection.execute(
                """
                select price, rsi14, ema200, trend_regime
                from market_snapshots
                where run_id = ? and symbol = ?
                limit 1
                """,
                (buy["run_id"], buy["symbol"]),
            ).fetchone()
            proposal = self.connection.execute(
                """
                select reason
                from ai_proposals
                where run_id = ? and symbol = ?
                limit 1
                """,
                (buy["run_id"], buy["symbol"]),
            ).fetchone()
            rsi = Decimal(str(snapshot["rsi14"])) if snapshot is not None and snapshot["rsi14"] is not None else None
            ema200 = Decimal(str(snapshot["ema200"])) if snapshot is not None and snapshot["ema200"] is not None else None
            snapshot_price = Decimal(str(snapshot["price"])) if snapshot is not None and snapshot["price"] is not None else None
            price_vs_ema = (
                self._safe_pct(snapshot_price - ema200, ema200)
                if snapshot_price is not None and ema200 is not None and ema200 != 0
                else None
            )
            cycles.append(
                ClosedTradeMemory(
                    symbol=str(buy["symbol"]),
                    buy_run_id=int(buy["run_id"]),
                    entry_price=entry_price,
                    exit_price=exit_price,
                    pnl_quote=pnl,
                    pnl_pct=self._safe_pct(pnl, allocated_buy_quote),
                    entry_trend_regime=str(snapshot["trend_regime"]) if snapshot is not None else "UNKNOWN",
                    entry_rsi14=rsi,
                    entry_price_vs_ema200_pct=price_vs_ema,
                    proposal_reason=str(proposal["reason"]) if proposal is not None else "",
                )
            )
            if len(cycles) >= max_cycles:
                break

        wins = sum(1 for cycle in cycles if cycle.pnl_quote > 0)
        losses = sum(1 for cycle in cycles if cycle.pnl_quote < 0)
        total_pnl = sum((cycle.pnl_quote for cycle in cycles), Decimal("0"))
        summary = (
            f"{len(cycles)} recent closed live cycle(s): {wins} win(s), {losses} loss(es), "
            f"realized PnL {total_pnl} quote units."
            if cycles
            else "No closed live cycles are available for AI decision memory yet."
        )
        return AiDecisionMemory(True, len(cycles), wins, losses, total_pnl, tuple(cycles), summary)

    def _safe_div(self, numerator: Decimal, denominator: Decimal) -> Decimal:
        if denominator == 0:
            return Decimal("0")
        return numerator / denominator

    def _safe_pct(self, pnl: Decimal, base: Decimal) -> Decimal:
        if base == 0:
            return Decimal("0")
        return pnl / base * Decimal("100")

    def _exit_preview(self, current_price: Decimal | None, stop_loss: Decimal, take_profit: Decimal) -> tuple[str, str]:
        if current_price is None:
            return "UNKNOWN_PRICE", "No current market snapshot is available for this live position."
        if stop_loss > 0 and current_price <= stop_loss:
            return "STOP_LOSS_REVIEW", "Current price is at or below the configured stop-loss threshold. Review guarded SELL."
        if take_profit > 0 and current_price >= take_profit:
            return "TAKE_PROFIT_REVIEW", "Current price is at or above the configured take-profit threshold. Review guarded SELL."
        return "HOLD", "Position is between stop-loss and take-profit thresholds."

    def cleanup_old_runs(self, keep_last: int) -> int:
        if keep_last <= 0:
            return 0
        old_rows = self.connection.execute(
            """
            select id
            from runs
            where id not in (
                select id from runs order by id desc limit ?
            )
            """,
            (keep_last,),
        ).fetchall()
        old_ids = [int(row["id"]) for row in old_rows]
        if not old_ids:
            return 0
        placeholders = ",".join("?" for _ in old_ids)
        tables = [
            "balances",
            "portfolio_valuations",
            "portfolio_summaries",
            "market_snapshots",
            "market_research_reports",
            "market_research_symbols",
            "ai_proposals",
            "shadow_signals",
            "risk_decisions",
            "paper_orders",
            "testnet_orders",
            "live_orders",
            "grid_recommendations",
            "strategy_decisions",
            "capital_sourcing_plans",
            "capital_sourcing_items",
            "trading_bankroll_reports",
            "earn_redeem_plans",
            "next_run_recommendations",
            "recommended_actions",
            "execution_checklist_items",
            "ai_commentaries",
            "research_notes",
            "research_statuses",
            "active_grid_evaluations",
        ]
        for table in tables:
            self.connection.execute(f"delete from {table} where run_id in ({placeholders})", old_ids)
        self.connection.execute(f"delete from runs where id in ({placeholders})", old_ids)
        self.connection.commit()
        return len(old_ids)

    def save_grid_recommendation(self, run_id: int, recommendation: GridRecommendation) -> None:
        self.connection.execute(
            "insert into grid_recommendations values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                int(recommendation.recommended),
                recommendation.symbol,
                recommendation.reason,
                str(recommendation.range_low),
                str(recommendation.range_high),
                recommendation.grid_count,
                str(recommendation.investment_usdt),
                str(recommendation.stop_loss_price),
                str(recommendation.take_profit_price),
            ),
        )
        self.connection.commit()

    def save_strategy_decision(self, run_id: int, decision: StrategyDecision) -> None:
        self.connection.execute(
            "insert into strategy_decisions values (?, ?, ?, ?, ?)",
            (run_id, decision.decision_type, decision.priority, decision.summary, decision.rebalancing_note),
        )
        self.connection.commit()

    def save_capital_sourcing_plan(self, run_id: int, plan_type: str, plan: CapitalSourcingPlan) -> None:
        self.connection.execute(
            "insert into capital_sourcing_plans values (?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                plan_type,
                str(plan.needed_usdt),
                str(plan.available_usdt),
                str(plan.missing_usdt),
                int(plan.recommended),
                plan.summary,
            ),
        )
        self.connection.executemany(
            """
            insert into capital_sourcing_items (
                run_id,
                plan_type,
                asset,
                action,
                value_usdt,
                source_pct_of_asset,
                remaining_value_usdt,
                remaining_pct_of_asset,
                reason
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    plan_type,
                    item.asset,
                    item.action,
                    str(item.value_usdt),
                    str(item.source_pct_of_asset),
                    str(item.remaining_value_usdt),
                    str(item.remaining_pct_of_asset),
                    item.reason,
                )
                for item in plan.items
            ],
        )
        self.connection.commit()

    def save_trading_bankroll_report(self, run_id: int, report: TradingBankrollReport) -> None:
        self.connection.execute(
            """
            insert into trading_bankroll_reports (
                run_id,
                enabled,
                quote_asset,
                initial_seed,
                spot_free,
                flexible_amount,
                total_quote,
                realized_pnl,
                profit_available,
                seed_capital_at_risk,
                required_amount,
                preferred_source,
                max_profit_trade_amount,
                flexible_draw_needed,
                summary
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                int(report.enabled),
                report.quote_asset,
                str(report.initial_seed),
                str(report.spot_free),
                str(report.flexible_amount),
                str(report.total_quote),
                str(report.realized_pnl),
                str(report.profit_available),
                str(report.seed_capital_at_risk),
                str(report.required_amount),
                report.preferred_source,
                str(report.max_profit_trade_amount),
                str(report.flexible_draw_needed),
                report.summary,
            ),
        )
        self.connection.commit()

    def save_earn_redeem_plan(self, run_id: int, plan: EarnRedeemPlan) -> None:
        self.connection.execute(
            """
            insert into earn_redeem_plans (
                run_id,
                enabled,
                asset,
                amount,
                status,
                product_id,
                redeem_type,
                can_redeem,
                submitted,
                confirmation_required,
                message
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                int(plan.enabled),
                plan.asset,
                str(plan.amount),
                plan.status,
                plan.product_id,
                plan.redeem_type,
                int(plan.can_redeem),
                int(plan.submitted),
                plan.confirmation_required,
                plan.message,
            ),
        )
        self.connection.commit()

    def save_next_run_recommendation(self, run_id: int, recommendation: NextRunRecommendation) -> None:
        self.connection.execute(
            "insert into next_run_recommendations values (?, ?, ?, ?, ?)",
            (
                run_id,
                recommendation.run_again_in_hours,
                recommendation.urgency,
                recommendation.reason,
                "\n".join(recommendation.triggers),
            ),
        )
        self.connection.commit()

    def save_recommended_actions(self, run_id: int, actions: tuple[RecommendedAction, ...]) -> None:
        self.connection.executemany(
            "insert into recommended_actions values (?, ?, ?, ?)",
            [(run_id, action.priority, action.action, action.reason) for action in actions],
        )
        self.connection.commit()

    def save_execution_checklist(self, run_id: int, items: tuple[ExecutionChecklistItem, ...]) -> None:
        self.connection.executemany(
            "insert into execution_checklist_items values (?, ?, ?, ?)",
            [(run_id, item.priority, item.step, item.detail) for item in items],
        )
        self.connection.commit()

    def save_ai_commentary(self, run_id: int, commentary: AiCommentary) -> None:
        self.connection.execute(
            "insert into ai_commentaries values (?, ?, ?, ?, ?, ?)",
            (
                run_id,
                int(commentary.enabled),
                commentary.summary,
                "\n".join(commentary.risks),
                "\n".join(commentary.watchlist),
                commentary.raw_response,
            ),
        )
        self.connection.commit()

    def save_research_notes(self, run_id: int, research: ResearchBundle) -> None:
        self.connection.executemany(
            "insert into research_notes values (?, ?, ?, ?)",
            [(run_id, note.source, note.title, note.content) for note in research.notes],
        )
        self.connection.commit()

    def save_research_status(self, run_id: int, status: ResearchStatus) -> None:
        self.connection.execute(
            "insert into research_statuses values (?, ?, ?, ?, ?, ?, ?)",
            (
                run_id,
                int(status.enabled),
                status.notes_count,
                int(status.is_fresh),
                str(status.latest_note_age_hours) if status.latest_note_age_hours is not None else None,
                status.request.path if status.request else None,
                status.summary,
            ),
        )
        self.connection.commit()

    def save_active_strategies(self, run_id: int, report: ActiveStrategiesReport) -> None:
        self.connection.executemany(
            "insert into active_grid_evaluations values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    run_id,
                    item.bot.name,
                    item.bot.symbol,
                    str(item.bot.range_low),
                    str(item.bot.range_high),
                    str(item.bot.investment_usdt),
                    str(item.current_price) if item.current_price is not None else None,
                    item.state,
                    str(item.distance_to_lower_pct) if item.distance_to_lower_pct is not None else None,
                    str(item.distance_to_upper_pct) if item.distance_to_upper_pct is not None else None,
                    item.recommendation,
                )
                for item in report.grid_bots
            ],
        )
        self.connection.commit()

    def _quote_asset(self, symbol: str) -> str:
        symbol = symbol.upper()
        for quote in ("USDC", "USDT", "FDUSD", "BTC", "ETH", "BNB"):
            if symbol.endswith(quote):
                return quote
        return "USDT"
