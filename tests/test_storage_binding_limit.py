"""The journal records why an approved order was the size it was.

Without this the size is recorded and the reason is not, so "why was this
order that big" can only be answered by re-deriving the arithmetic from a
config that may have changed since the run.

The migration matters as much as the column: every existing install has a
`risk_decisions` table without it, and a journal that cannot be opened after
an upgrade is worse than one missing a field.
"""

from decimal import Decimal

from trading_agent.models import RiskDecision
from trading_agent.storage import Storage


def _decision(binding_limit: str = "funding") -> RiskDecision:
    return RiskDecision(
        approved=True,
        reason="approved",
        adjusted_quote_amount_usdt=Decimal("11.89"),
        binding_limit=binding_limit,
    )


def _read(storage: Storage) -> list[tuple]:
    # The connection hands back sqlite3.Row; tuples compare readably.
    return [
        tuple(row)
        for row in storage.connection.execute(
            "select run_id, adjusted_quote_amount_usdt, binding_limit from risk_decisions"
        )
    ]


def test_the_binding_limit_is_written_with_the_decision(tmp_path) -> None:
    storage = Storage(tmp_path / "journal.sqlite3")
    run_id = storage.start_run("DRY_RUN")

    storage.save_risk_decision(run_id, _decision())

    assert _read(storage) == [(run_id, "11.89", "funding")]


def test_a_rejection_records_no_limit(tmp_path) -> None:
    storage = Storage(tmp_path / "journal.sqlite3")
    run_id = storage.start_run("DRY_RUN")

    storage.save_risk_decision(
        run_id,
        RiskDecision(approved=False, reason="hold", adjusted_quote_amount_usdt=Decimal("0")),
    )

    assert _read(storage) == [(run_id, "0", "")]


def test_a_journal_from_before_the_column_still_opens(tmp_path) -> None:
    """Every install upgrading to this version has one of these."""
    path = tmp_path / "old.sqlite3"
    first = Storage(path)
    first.connection.execute("alter table risk_decisions drop column binding_limit")
    first.connection.commit()
    first.connection.close()

    reopened = Storage(path)
    run_id = reopened.start_run("DRY_RUN")
    reopened.save_risk_decision(run_id, _decision("position_per_asset"))

    assert _read(reopened) == [(run_id, "11.89", "position_per_asset")]
