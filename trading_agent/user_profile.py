from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib

from .locale_profile import normalize_locale


PROFILE_VERSION = 1

ONBOARDING_PATHS = ("EXISTING_PORTFOLIO", "FIRST_PORTFOLIO")
SETUP_MODES = ("SAFE_DEFAULTS", "GUIDED", "ADVANCED")
EXPERIENCE_LEVELS = ("BEGINNER", "INTERMEDIATE", "ADVANCED")
MANAGEMENT_STYLES = ("CONSERVATIVE", "BALANCED", "ACTIVE")
AUTOMATION_LEVELS = ("RECOMMEND_ONLY", "GUARDED_AUTOMATION", "ACTIVE_AUTOMATION")
RUN_CADENCES = ("WEEKLY", "TWICE_WEEKLY", "DAILY", "MANUAL")
EXCHANGES = ("BINANCE",)


@dataclass(frozen=True)
class UserProfile:
    version: int
    onboarding_path: str
    exchange: str
    locale: str
    setup_mode: str
    experience: str
    management_style: str
    automation_level: str
    run_cadence: str
    base_currency: str
    planned_deposit_amount: float
    reserve_pct: float
    max_drawdown_comfort_pct: float
    use_earn: bool
    use_rebalancing: bool
    # Whether the user wants bot recommendations at all. use_grid is narrower:
    # it is only true when an Active style also asked for them.
    use_bots: bool
    use_grid: bool
    allow_spot_trades: bool
    wants_explanations: bool

    @property
    def summary(self) -> str:
        return (
            f"{self.setup_mode} {self.onboarding_path} on {self.exchange} ({self.locale}): {self.management_style}, "
            f"{self.automation_level}, run {self.run_cadence.lower()}."
        )


class UserProfileStore:
    def __init__(self, path: str | Path = "state/user_profile.toml"):
        self.path = Path(path)

    def load(self) -> UserProfile | None:
        if not self.path.exists():
            return None
        with self.path.open("rb") as handle:
            payload = tomllib.load(handle)
        profile = payload.get("user_profile", {})
        if not isinstance(profile, dict):
            return None
        return self._from_mapping(profile)

    def save(self, profile: UserProfile) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self._render(profile), encoding="utf-8")

    def delete(self) -> bool:
        if not self.path.exists():
            return False
        self.path.unlink()
        return True

    def save_safe_default(self, onboarding_path: str) -> UserProfile:
        profile = safe_default_profile(onboarding_path)
        self.save(profile)
        return profile

    def save_guided(
        self,
        onboarding_path: str,
        management_style: str,
        automation_level: str,
        run_cadence: str,
        base_currency: str,
        use_bots: bool,
        allow_spot_trades: bool,
        max_drawdown_comfort_pct: float,
        locale: str = "en-US",
        planned_deposit_amount: float = 0.0,
    ) -> UserProfile:
        profile = guided_profile(
            onboarding_path=onboarding_path,
            management_style=management_style,
            automation_level=automation_level,
            run_cadence=run_cadence,
            base_currency=base_currency,
            locale=locale,
            use_bots=use_bots,
            allow_spot_trades=allow_spot_trades,
            max_drawdown_comfort_pct=max_drawdown_comfort_pct,
            planned_deposit_amount=planned_deposit_amount,
        )
        self.save(profile)
        return profile

    def _from_mapping(self, values: dict) -> UserProfile:
        return UserProfile(
            version=int(values.get("version", PROFILE_VERSION)),
            onboarding_path=_choice(values.get("onboarding_path"), ONBOARDING_PATHS, "EXISTING_PORTFOLIO"),
            exchange=_choice(values.get("exchange"), EXCHANGES, "BINANCE"),
            locale=normalize_locale(values.get("locale")),
            setup_mode=_choice(values.get("setup_mode"), SETUP_MODES, "SAFE_DEFAULTS"),
            experience=_choice(values.get("experience"), EXPERIENCE_LEVELS, "BEGINNER"),
            management_style=_choice(values.get("management_style"), MANAGEMENT_STYLES, "CONSERVATIVE"),
            automation_level=_choice(values.get("automation_level"), AUTOMATION_LEVELS, "RECOMMEND_ONLY"),
            run_cadence=_choice(values.get("run_cadence"), RUN_CADENCES, "WEEKLY"),
            base_currency=str(values.get("base_currency", "USDC")).upper(),
            planned_deposit_amount=float(values.get("planned_deposit_amount", 0)),
            reserve_pct=float(values.get("reserve_pct", 20)),
            max_drawdown_comfort_pct=float(values.get("max_drawdown_comfort_pct", 10)),
            use_earn=bool(values.get("use_earn", True)),
            use_rebalancing=bool(values.get("use_rebalancing", True)),
            # Older profiles predate use_bots; fall back to use_grid so an
            # Active user who enabled bots keeps them after the upgrade.
            use_bots=bool(values.get("use_bots", values.get("use_grid", False))),
            use_grid=bool(values.get("use_grid", False)),
            allow_spot_trades=bool(values.get("allow_spot_trades", False)),
            wants_explanations=bool(values.get("wants_explanations", True)),
        )

    def _render(self, profile: UserProfile) -> str:
        return "\n".join(
            [
                "# Coinductor user onboarding profile.",
                "# Safe defaults are conservative and can be replaced by guided or advanced setup.",
                "",
                "[user_profile]",
                f"version = {profile.version}",
                f'onboarding_path = "{profile.onboarding_path}"',
                f'exchange = "{profile.exchange}"',
                f'locale = "{profile.locale}"',
                f'setup_mode = "{profile.setup_mode}"',
                f'experience = "{profile.experience}"',
                f'management_style = "{profile.management_style}"',
                f'automation_level = "{profile.automation_level}"',
                f'run_cadence = "{profile.run_cadence}"',
                f'base_currency = "{profile.base_currency}"',
                f"planned_deposit_amount = {profile.planned_deposit_amount:.2f}",
                f"reserve_pct = {profile.reserve_pct:.2f}",
                f"max_drawdown_comfort_pct = {profile.max_drawdown_comfort_pct:.2f}",
                f"use_earn = {_toml_bool(profile.use_earn)}",
                f"use_rebalancing = {_toml_bool(profile.use_rebalancing)}",
                f"use_bots = {_toml_bool(profile.use_bots)}",
                f"use_grid = {_toml_bool(profile.use_grid)}",
                f"allow_spot_trades = {_toml_bool(profile.allow_spot_trades)}",
                f"wants_explanations = {_toml_bool(profile.wants_explanations)}",
                "",
            ]
        )


def safe_default_profile(onboarding_path: str) -> UserProfile:
    normalized = _choice(onboarding_path, ONBOARDING_PATHS, "EXISTING_PORTFOLIO")
    return UserProfile(
        version=PROFILE_VERSION,
        onboarding_path=normalized,
        exchange="BINANCE",
        locale="en-US",
        setup_mode="SAFE_DEFAULTS",
        experience="BEGINNER",
        management_style="CONSERVATIVE",
        automation_level="RECOMMEND_ONLY",
        run_cadence="WEEKLY",
        base_currency="USDC",
        planned_deposit_amount=0.0,
        reserve_pct=20.0,
        max_drawdown_comfort_pct=10.0,
        use_earn=True,
        use_rebalancing=True,
        use_bots=False,
        use_grid=False,
        allow_spot_trades=False,
        wants_explanations=True,
    )


def guided_profile(
    onboarding_path: str,
    management_style: str,
    automation_level: str,
    run_cadence: str,
    base_currency: str,
    use_bots: bool,
    allow_spot_trades: bool,
    max_drawdown_comfort_pct: float,
    locale: str = "en-US",
    planned_deposit_amount: float = 0.0,
) -> UserProfile:
    normalized_path = _choice(onboarding_path, ONBOARDING_PATHS, "EXISTING_PORTFOLIO")
    style = _choice(management_style, MANAGEMENT_STYLES, "BALANCED")
    automation = _choice(automation_level, AUTOMATION_LEVELS, "RECOMMEND_ONLY")
    if automation == "ACTIVE_AUTOMATION":
        automation = "GUARDED_AUTOMATION"
    cadence = _choice(run_cadence, RUN_CADENCES, _cadence_for_style(style))
    # 0 is the "off" sentinel: the user asked the wizard not to touch the loss
    # limits in config.toml at all, so it must survive the 5..25 clamp.
    drawdown = (
        0.0
        if _is_drawdown_off(max_drawdown_comfort_pct)
        else _bounded_float(max_drawdown_comfort_pct, minimum=5.0, maximum=25.0, default=_drawdown_for_style(style))
    )
    currency = str(base_currency or "USDC").strip().upper() or "USDC"
    normalized_locale = normalize_locale(locale)
    deposit = _bounded_float(planned_deposit_amount, minimum=0.0, maximum=1_000_000.0, default=0.0)
    spot_allowed = bool(allow_spot_trades and automation == "GUARDED_AUTOMATION")
    bots_enabled = bool(use_bots)

    return UserProfile(
        version=PROFILE_VERSION,
        onboarding_path=normalized_path,
        exchange="BINANCE",
        locale=normalized_locale,
        setup_mode="GUIDED",
        experience=_experience_for_style(style),
        management_style=style,
        automation_level=automation,
        run_cadence=cadence,
        base_currency=currency,
        planned_deposit_amount=deposit,
        reserve_pct=_reserve_for_style(style),
        max_drawdown_comfort_pct=drawdown,
        use_earn=True,
        use_rebalancing=True,
        use_bots=bots_enabled,
        use_grid=bots_enabled and style == "ACTIVE",
        allow_spot_trades=spot_allowed,
        wants_explanations=True,
    )


def _choice(value: object, allowed: tuple[str, ...], default: str) -> str:
    normalized = str(value or "").upper()
    return normalized if normalized in allowed else default


def _bounded_float(value: object, minimum: float, maximum: float, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return min(max(number, minimum), maximum)


def _cadence_for_style(style: str) -> str:
    if style == "ACTIVE":
        return "DAILY"
    if style == "BALANCED":
        return "TWICE_WEEKLY"
    return "WEEKLY"


def _is_drawdown_off(value: object) -> bool:
    try:
        return float(value) == 0.0
    except (TypeError, ValueError):
        return False


def _drawdown_for_style(style: str) -> float:
    if style == "ACTIVE":
        return 20.0
    if style == "BALANCED":
        return 15.0
    return 10.0


def _experience_for_style(style: str) -> str:
    if style == "ACTIVE":
        return "INTERMEDIATE"
    return "BEGINNER"


def _reserve_for_style(style: str) -> float:
    if style == "ACTIVE":
        return 12.0
    if style == "BALANCED":
        return 16.0
    return 22.0


def _toml_bool(value: bool) -> str:
    return "true" if value else "false"
