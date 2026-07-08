from __future__ import annotations

from pathlib import Path
import re
import sqlite3

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
        try:
            latest = self._latest_real_run(connection)
            latest_result = None
            portfolio: tuple[dict[str, str], ...] = ()
            strategies: tuple[dict[str, str], ...] = ()
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
            history = self._history(connection)
            return DesktopSnapshot(latest_result, portfolio, strategies, history)
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
                       {self._column_expr(grid_columns, "blockers")}
                from grid_recommendations where run_id = ?
                """,
                (run_id,),
            ).fetchone()
            if grid is not None:
                strategies.append(
                    {
                        "type": "Spot Grid",
                        "name": str(grid["symbol"] or "No candidate"),
                        "status": str(grid["market_status"] or "UNKNOWN"),
                        "capital": self._money(grid["investment_usdt"]),
                        "allowed": "Ready" if grid["deployment_allowed"] else "Blocked",
                        "detail": str(grid["reason"] or ""),
                        "parameters": (
                            {"label": "Symbol", "value": str(grid["symbol"] or "")},
                            {"label": "Range", "value": self._range(grid["range_low"], grid["range_high"])},
                            {"label": "Grids", "value": str(grid["grid_count"] or "")},
                            {"label": "Investment", "value": self._money(grid["investment_usdt"])},
                            {"label": "Spacing", "value": self._percent(grid["estimated_grid_spacing_pct"])},
                            {"label": "TP / SL", "value": self._range(grid["take_profit_price"], grid["stop_loss_price"])},
                            {"label": "Blockers", "value": str(grid["blockers"] or "")},
                        ),
                    }
                )
        if self._table_exists(connection, "rebalancing_bot_recommendations"):
            rebalance_columns = self._columns(connection, "rebalancing_bot_recommendations")
            rebalance = connection.execute(
                f"""
                select deployment_allowed, mode, threshold_pct, investment_usdt, summary,
                       {self._column_expr(rebalance_columns, "blockers")}
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
                        "allowed": f"Ratio {rebalance['threshold_pct']}%",
                        "detail": str(rebalance["summary"] or ""),
                        "parameters": (
                            {"label": "Mode", "value": str(rebalance["mode"] or "THRESHOLD")},
                            {"label": "Investment", "value": self._money(rebalance["investment_usdt"])},
                            {"label": "Threshold", "value": self._percent(rebalance["threshold_pct"])},
                            {"label": "Basket", "value": basket},
                            {"label": "Blockers", "value": str(rebalance["blockers"] or "")},
                        ),
                    }
                )
        return tuple(strategies)

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
                "startedAt": str(row["started_at"]),
                "status": str(row["status"]),
                "dataMode": "MOCK" if row["data_status"] == "MOCK" else "REAL",
                "decision": str(row["decision_type"] or "UNKNOWN"),
                "summary": str(row["decision_summary"] or row["summary"] or ""),
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

    def _table_exists(self, connection: sqlite3.Connection, table: str) -> bool:
        row = connection.execute(
            "select name from sqlite_master where type = 'table' and name = ?",
            (table,),
        ).fetchone()
        return row is not None

    def _columns(self, connection: sqlite3.Connection, table: str) -> set[str]:
        rows = connection.execute(f"pragma table_info({table})").fetchall()
        return {str(row["name"]) for row in rows}

    def _column_expr(self, columns: set[str], column: str) -> str:
        return column if column in columns else f"null as {column}"

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
