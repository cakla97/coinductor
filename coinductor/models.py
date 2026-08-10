from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from trading_agent.config import default_config_path


@dataclass(frozen=True)
class RunOptions:
    config_path: str = field(default_factory=default_config_path)
    data_mode: str = "REAL"
    ai_summary: bool = True
    ai_proposals: bool = False
    live_preview: bool = True
    live_submit: bool = False
    live_confirm: str = ""
    oco_submit: bool = False
    oco_confirm: str = ""
    earn_redeem_submit: bool = False
    earn_redeem_confirm: str = ""
    manual_override_symbol: str = ""
    response_language: str = "en"


@dataclass(frozen=True)
class ActionSummary:
    priority: str
    action: str
    reason: str


@dataclass(frozen=True)
class DesktopRunResult:
    run_id: int
    status: str
    report_path: str
    decision: str
    decision_summary: str
    risk_approved: bool
    risk_reason: str
    portfolio_value: Decimal
    liquid_value: Decimal
    locked_value: Decimal
    ai_summary: str
    actions: tuple[ActionSummary, ...]
    trade_proposal: dict[str, str] | None = None
    # Whether the run asked the model at all. Without this the desktop cannot
    # tell "the model said nothing useful" from "you ran this without AI", and
    # showed the engine's English note for both.
    ai_enabled: bool = True
    # Empty for a run recorded before the report carried it, and for a summary
    # that is ours rather than the model's - both mean "nothing to explain".
    ai_language: str = ""
    # Which ceiling produced the approved order size, as the machine key the
    # journal stores. Empty for a rejected proposal and for any run from before
    # sizing recorded it; the screen shows nothing rather than guessing.
    binding_limit: str = ""


@dataclass(frozen=True)
class DesktopSnapshot:
    latest_run: DesktopRunResult | None
    portfolio_assets: tuple[dict[str, str], ...]
    strategies: tuple[dict[str, str], ...]
    run_history: tuple[dict[str, str], ...]
    position_protection: dict[str, object] | None = None
    has_ready_live_preview: bool = False
    live_action_lifecycle: dict[str, object] | None = None
    active_strategies: tuple[dict[str, object], ...] = ()
    active_strategies_summary: str = "No active strategies are registered."
    next_review: dict[str, object] | None = None
    earn_redeem: dict[str, object] | None = None
    # Read from the journal rather than parsed back out of the Markdown report,
    # so each item still carries the message it was composed from.
    recommended_actions: tuple[dict[str, object], ...] = ()
    risk_reason_message: tuple[dict[str, object], ...] = ()
    decision_summary_message: tuple[dict[str, object], ...] = ()


@dataclass(frozen=True)
class SetupSnapshot:
    checks: tuple[dict[str, str], ...]
    passed: int
    warnings: int
    blocked: int


@dataclass(frozen=True)
class ConnectionCheckResult:
    status: str
    detail: str


@dataclass(frozen=True)
class AiProviderSnapshot:
    summary: str
    checks: tuple[dict[str, str], ...]
    context_sections: tuple[dict[str, str], ...]
    base_url: str = ""
    text_model: str = ""
    vision_model: str = ""


@dataclass(frozen=True)
class AiProviderHealthResult:
    status: str
    detail: str


@dataclass(frozen=True)
class AiModelDiscoveryResult:
    status: str
    detail: str
    models: tuple[str, ...] = ()


@dataclass(frozen=True)
class UserProfileSnapshot:
    configured: bool
    summary: str
    fields: tuple[dict[str, str], ...]
    exchange_steps: tuple[dict[str, str], ...] = ()


@dataclass(frozen=True)
class SafetySnapshot:
    stage: str
    label: str
    detail: str
    allows_live_preview: bool
    allows_live_submit: bool
    checks: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class ReadinessSnapshot:
    summary: str
    next_step: str
    action_code: str
    action_label: str
    action_enabled: bool
    steps: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class FirstPortfolioPlanSnapshot:
    available: bool
    summary: str
    funding: tuple[dict[str, str], ...]
    allocation: tuple[dict[str, object], ...]
    steps: tuple[dict[str, str], ...]
    notes: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class LocalDataResetSnapshot:
    summary: str
    items: tuple[dict[str, str], ...]
