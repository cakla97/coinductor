"""The decision-profile choices, with what each one actually does.

The wizard used to carry these lists and their help text as English literals
inside ``Main.qml``, so they could not be translated and nothing tied the help
text to the code that consumes the choice. Building them here keeps one source
of truth: the label, the explanation, and the value the engine reads all live
next to each other, and both languages come from :mod:`ui_strings`.

Help text is written to answer "what does picking this change", not "what does
this word mean" - a user should be able to read it and predict the behaviour.
"""

from __future__ import annotations

from .risk_profile import DRAWDOWN_OFF, describe_drawdown, describe_gates
from .ui_strings import UiStringsService

# value -> (label key, help key). Values are the identifiers the engine stores;
# never translate them.
# Style help is generated from the gate table, like drawdown, so it cannot
# advertise a filter the wizard does not write.
STYLE_LABEL_KEYS = {
    "CONSERVATIVE": "opt_style_conservative",
    "BALANCED": "opt_style_balanced",
    "ACTIVE": "opt_style_active",
}

AUTOMATION_CHOICES = (
    ("RECOMMEND_ONLY", "opt_automation_recommend", "help_automation_recommend"),
    ("GUARDED_AUTOMATION", "opt_automation_guarded", "help_automation_guarded"),
)

CADENCE_CHOICES = (
    ("WEEKLY", "opt_cadence_weekly", "help_cadence_weekly"),
    ("TWICE_WEEKLY", "opt_cadence_twice_weekly", "help_cadence_twice_weekly"),
    ("DAILY", "opt_cadence_daily", "help_cadence_daily"),
    ("MANUAL", "opt_cadence_manual", "help_cadence_manual"),
)

# Drawdown help is generated from the loss-cap table rather than written out, so
# the wizard can never advertise limits it does not write.
DRAWDOWN_CHOICES = (DRAWDOWN_OFF, 10, 15, 20)

DRAWDOWN_LABEL_KEYS = {
    DRAWDOWN_OFF: "opt_drawdown_off",
    10: "opt_drawdown_low",
    15: "opt_drawdown_medium",
    20: "opt_drawdown_high",
}

BUDGET_CHOICES = (0, 250, 500, 1000, 2000, 10000, 25000)


def _text(language: str) -> dict[str, str]:
    return UiStringsService().wizard_text(language)


def _options(choices, language: str) -> list[dict[str, object]]:
    text = _text(language)
    return [
        {"value": value, "label": text.get(label_key, label_key), "help": text.get(help_key, "")}
        for value, label_key, help_key in choices
    ]


def profile_choices(language: str) -> dict[str, list[dict[str, object]]]:
    """Every decision-profile dropdown, localized, with per-option help."""
    text = _text(language)
    return {
        "style": [
            {
                "value": value,
                "label": text.get(key, value.title()),
                "help": describe_gates(value, language),
            }
            for value, key in STYLE_LABEL_KEYS.items()
        ],
        "automation": _options(AUTOMATION_CHOICES, language),
        "cadence": _options(CADENCE_CHOICES, language),
        "drawdown": [
            {
                "value": value,
                "label": text.get(DRAWDOWN_LABEL_KEYS[value], str(value)),
                "help": describe_drawdown(value, language),
            }
            for value in DRAWDOWN_CHOICES
        ],
        "budget": [
            {
                "value": value,
                "label": text.get("opt_budget_auto", "Auto") if value == 0 else f"{value:,}",
                "help": "",
            }
            for value in BUDGET_CHOICES
        ],
    }


def toggle_help(language: str) -> dict[str, str]:
    """Help text for the two checkboxes, keyed by ``<name>_<on|off>``."""
    text = _text(language)
    return {
        "bots_on": text.get("help_bots_on", ""),
        "bots_off": text.get("help_bots_off", ""),
        "spot_on": text.get("help_spot_on", ""),
        "spot_off": text.get("help_spot_off", ""),
    }
