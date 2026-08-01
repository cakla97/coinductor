"""Permission to submit an order with nobody in the room.

This is the only thing in Coinductor that can put an order on a real exchange
without a person present, so it is built to be reasoned about rather than to be
convenient. Its tests were written before it was, and they are the
specification: see tests/test_coinductor_standing_authorisation.py.

The default answer is no, and stays no unless *all* of these hold:

  - an authorisation exists, is not revoked, and has not expired
  - the symbol matches exactly
  - the side is BUY, which is the only side that can be authorised
  - the order is within the per-order cap
  - the order plus everything already spent is within the window cap
  - the safety stage is LIVE_ENABLED

Nothing here decides *whether* an order is a good idea - the risk engine still
does that, first and independently. This only decides whether the human's
absence is excused, and every refusal names which gate said no so the journal
can record it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
import tomllib

DEFAULT_PATH = "state/standing_authorisation.toml"

# A window is re-armed by hand. Long enough to be useful over a holiday, short
# enough that nobody is running on a permission they granted last spring.
MAX_WINDOW_DAYS = 14

# The stage that has to be reached by hand, on screen, before any live submit is
# possible at all. Reused rather than paralleled: a second notion of "armed"
# would be a second thing to get wrong.
REQUIRED_STAGE = "LIVE_ENABLED"


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class LiveAuthorisation:
    symbol: str
    side: str
    per_order_cap: Decimal
    window_cap: Decimal
    spent: Decimal
    granted_at: datetime
    expires_at: datetime

    @property
    def remaining(self) -> Decimal:
        return max(Decimal("0"), self.window_cap - self.spent)


def evaluate(
    authorisation: LiveAuthorisation | None,
    *,
    symbol: str,
    side: str,
    amount: Decimal,
    now: datetime,
    safety_stage: str,
) -> Decision:
    """Whether this specific order may go without a person present.

    Ordered so the answer names the first thing that failed, which is what a
    reader wants: "the wrong symbol" is more useful than "not permitted".
    """
    if authorisation is None:
        return Decision(False, "standing_none")
    if now >= authorisation.expires_at:
        return Decision(False, "standing_expired")
    if str(symbol).strip().upper() != authorisation.symbol:
        return Decision(False, "standing_other_symbol")
    if str(side).strip().upper() != authorisation.side:
        return Decision(False, "standing_other_side")
    if str(safety_stage).strip().upper() != REQUIRED_STAGE:
        return Decision(False, "standing_stage")
    if amount > authorisation.per_order_cap:
        # Refused, not shrunk. Truncating an order nobody is watching turns
        # "I authorised 50" into an unbounded stream of 50s.
        return Decision(False, "standing_over_order_cap")
    if authorisation.spent + amount > authorisation.window_cap:
        return Decision(False, "standing_over_window_cap")
    return Decision(True, "standing_allowed")


class StandingAuthorisationStore:
    def __init__(self, path: str | Path = DEFAULT_PATH):
        self.path = Path(path)

    def grant(
        self,
        *,
        symbol: str,
        side: str,
        per_order_cap: Decimal,
        window_cap: Decimal,
        days: int,
        now: datetime,
    ) -> LiveAuthorisation:
        """Create one, replacing any existing. Raises rather than clamping.

        Everything else in this app clamps a bad number into range, because a
        refused setting is a worse outcome than a corrected one. Here it is the
        other way round: silently turning a mistyped cap into a working
        permission is exactly the accident this guards against.
        """
        normalized = str(symbol).strip().upper()
        direction = str(side).strip().upper()
        if not normalized:
            raise ValueError("A symbol is required.")
        if direction != "BUY":
            raise ValueError("Only BUY can be authorised; selling is how someone exits.")
        if per_order_cap <= 0 or window_cap <= 0:
            raise ValueError("Caps must be greater than zero.")
        if per_order_cap > window_cap:
            raise ValueError("A per-order cap above the window cap is not a cap.")
        if days <= 0 or days > MAX_WINDOW_DAYS:
            raise ValueError(f"A window must be between 1 and {MAX_WINDOW_DAYS} days.")

        expires_at = now + timedelta(days=int(days))
        # Replaces rather than appends: two live authorisations would make the
        # window cap meaningless, and a new grant resets the spend on purpose.
        self._write(
            symbol=normalized,
            side=direction,
            per_order_cap=per_order_cap,
            window_cap=window_cap,
            spent=Decimal("0"),
            granted_at=now,
            expires_at=expires_at,
        )
        return LiveAuthorisation(
            normalized, direction, per_order_cap, window_cap, Decimal("0"), now, expires_at
        )

    def current(self, *, now: datetime) -> LiveAuthorisation | None:
        """The authorisation if it is still live, else None. For display."""
        stored = self.stored()
        return None if stored is None or now >= stored.expires_at else stored

    def stored(self) -> LiveAuthorisation | None:
        """Whatever is on disk, expired or not. For the gate.

        Kept apart from `current` because the two want different things: a
        screen showing a dead permission would be misleading, but a refusal
        that says "expired" is far more use than one that says "none" - and
        that distinction is only available to a caller that can see it.
        """
        payload = self._read()
        if not payload:
            return None
        try:
            expires_at = datetime.fromisoformat(str(payload["expires_at"]))
            granted_at = datetime.fromisoformat(str(payload["granted_at"]))
            authorisation = LiveAuthorisation(
                symbol=str(payload["symbol"]).upper(),
                side=str(payload["side"]).upper(),
                per_order_cap=Decimal(str(payload["per_order_cap"])),
                window_cap=Decimal(str(payload["window_cap"])),
                spent=Decimal(str(payload.get("spent", "0"))),
                granted_at=granted_at,
                expires_at=expires_at,
            )
        except (KeyError, ValueError, InvalidOperation, TypeError):
            return None
        return authorisation

    def record_use(self, amount: Decimal, *, now: datetime) -> None:
        """Add to the running total. Persisted, so a restart cannot reset it."""
        authorisation = self.current(now=now)
        if authorisation is None:
            return
        self._write(
            symbol=authorisation.symbol,
            side=authorisation.side,
            per_order_cap=authorisation.per_order_cap,
            window_cap=authorisation.window_cap,
            spent=authorisation.spent + amount,
            granted_at=authorisation.granted_at,
            expires_at=authorisation.expires_at,
        )

    def revoke(self) -> None:
        """Take it back. Deletes rather than flags: nothing left to misread."""
        if self.path.exists():
            self.path.unlink()

    def _read(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            payload = tomllib.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            # Fail closed. An unreadable permission is not a permission.
            return {}
        section = payload.get("standing_authorisation", {})
        return section if isinstance(section, dict) else {}

    def _write(self, **values: object) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        body = "\n".join(
            f'{key} = "{value}"' for key, value in values.items()
        )
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            "# Permission for Coinductor to submit without you present.\n"
            "# Delete this file to revoke it immediately.\n\n"
            f"[standing_authorisation]\nversion = 1\n{body}\n",
            encoding="utf-8",
        )
        temporary.replace(self.path)


def utcnow() -> datetime:
    return datetime.now(UTC)
