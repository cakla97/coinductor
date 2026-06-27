from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class RunOptions:
    config_path: str = "config.example.toml"
    data_mode: str = "REAL"
    ai_summary: bool = True
    ai_proposals: bool = False
    live_preview: bool = True


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


@dataclass(frozen=True)
class DesktopSnapshot:
    latest_run: DesktopRunResult | None
    portfolio_assets: tuple[dict[str, str], ...]
    strategies: tuple[dict[str, str], ...]
    run_history: tuple[dict[str, str], ...]


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


@dataclass(frozen=True)
class AiProviderHealthResult:
    status: str
    detail: str


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
    allocation: tuple[dict[str, str], ...]
    steps: tuple[dict[str, str], ...]
    notes: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class LocalDataResetSnapshot:
    summary: str
    items: tuple[dict[str, str], ...]
