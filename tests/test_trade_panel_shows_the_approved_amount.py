"""The Trade screen shows the order, not only the request.

Taken from a real journal: the model proposed 77.00 USDC and the risk engine
approved 11.90, bound by what the account could actually pay. The screen showed
77.00 - directly above the button that submits the order - and never mentioned
the number that would have been sent. Both figures now appear, in that order.
"""

from decimal import Decimal

from coinductor.desktop_store import DesktopStore
from trading_agent.models import RiskDecision
from trading_agent.storage import Storage


def _journal(tmp_path, *, approved: bool, amount: str = "11.90", binding: str = "funding"):
    storage = Storage(tmp_path / "journal.sqlite3")
    run_id = storage.start_run("DRY_RUN")
    storage.save_risk_decision(
        run_id,
        RiskDecision(
            approved=approved,
            reason="approved" if approved else "rejected",
            adjusted_quote_amount_usdt=Decimal(amount),
            binding_limit=binding,
        ),
    )
    return storage, run_id


def _sizing(tmp_path, storage, run_id) -> tuple[str, str]:
    store = DesktopStore(
        database_path=tmp_path / "journal.sqlite3",
        reports_dir=tmp_path / "reports",
    )
    return store._risk_sizing(storage.connection, run_id)


def test_the_approved_amount_is_read_back_with_its_reason(tmp_path) -> None:
    storage, run_id = _journal(tmp_path, approved=True)

    binding, approved = _sizing(tmp_path, storage, run_id)

    assert approved == "11.90 USDC"
    assert binding == "funding"


def test_a_rejected_proposal_reports_no_approved_amount(tmp_path) -> None:
    """A refused order has no size; a number here would suggest it had one."""
    storage, run_id = _journal(tmp_path, approved=False)

    _binding, approved = _sizing(tmp_path, storage, run_id)

    assert approved == ""


def test_a_journal_without_the_binding_column_still_reads(tmp_path) -> None:
    storage, run_id = _journal(tmp_path, approved=True)
    storage.connection.execute("alter table risk_decisions drop column binding_limit")

    binding, approved = _sizing(tmp_path, storage, run_id)

    assert binding == ""
    assert approved == "11.90 USDC"
