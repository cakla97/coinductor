from __future__ import annotations

from pathlib import Path
import sqlite3

from .models import AiCommentary, Balance, CapitalSourcingPlan, GridRecommendation, MarketSnapshot, NextRunRecommendation, PortfolioAnalysis, RecommendedAction, ResearchBundle, RiskDecision, StrategyDecision, TradeProposal


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
            create table if not exists ai_proposals (
                run_id integer,
                symbol text,
                action text,
                confidence text,
                quote_amount_usdt text,
                reason text
            );
            create table if not exists risk_decisions (
                run_id integer,
                approved integer,
                reason text,
                adjusted_quote_amount_usdt text
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
                reason text
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
            """
        )
        self._ensure_column("portfolio_summaries", "unpriced_assets", "text")
        self._ensure_column("portfolio_summaries", "ignored_internal_assets", "text")
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
        return 0

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
            "insert into portfolio_valuations values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    run_id,
                    asset.asset,
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

    def save_proposal(self, run_id: int, proposal: TradeProposal) -> None:
        self.connection.execute(
            "insert into ai_proposals values (?, ?, ?, ?, ?, ?)",
            (run_id, proposal.symbol, proposal.action, str(proposal.confidence), str(proposal.quote_amount_usdt), proposal.reason),
        )
        self.connection.commit()

    def save_risk_decision(self, run_id: int, decision: RiskDecision) -> None:
        self.connection.execute(
            "insert into risk_decisions values (?, ?, ?, ?)",
            (run_id, int(decision.approved), decision.reason, str(decision.adjusted_quote_amount_usdt)),
        )
        self.connection.commit()

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
            "insert into capital_sourcing_items values (?, ?, ?, ?, ?, ?)",
            [(run_id, plan_type, item.asset, item.action, str(item.value_usdt), item.reason) for item in plan.items],
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
