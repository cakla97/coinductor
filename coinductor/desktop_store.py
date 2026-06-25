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

    def _strategies(self, connection: sqlite3.Connection, run_id: int) -> tuple[dict[str, str], ...]:
        strategies: list[dict[str, str]] = []
        grid = connection.execute(
            """
            select symbol, market_status, deployment_allowed, score, investment_usdt, reason
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
                }
            )
        rebalance = connection.execute(
            """
            select deployment_allowed, mode, threshold_pct, investment_usdt, summary
            from rebalancing_bot_recommendations where run_id = ?
            """,
            (run_id,),
        ).fetchone()
        if rebalance is not None:
            strategies.append(
                {
                    "type": "Rebalancing",
                    "name": str(rebalance["mode"] or "THRESHOLD"),
                    "status": "READY" if rebalance["deployment_allowed"] else "BLOCKED",
                    "capital": self._money(rebalance["investment_usdt"]),
                    "allowed": f"Ratio {rebalance['threshold_pct']}%",
                    "detail": str(rebalance["summary"] or ""),
                }
            )
        return tuple(strategies)

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
