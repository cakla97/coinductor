from __future__ import annotations

from pathlib import Path
import sqlite3

from .models import Balance, MarketSnapshot, RiskDecision, TradeProposal


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
            """
        )
        self.connection.commit()

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

