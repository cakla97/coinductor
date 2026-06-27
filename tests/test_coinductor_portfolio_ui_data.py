from coinductor.controller import _humanize_policy_label, _parse_money_value, _role_help


def test_policy_labels_are_user_facing() -> None:
    assert _humanize_policy_label("SYSTEM_DEFAULT") == "System default"
    assert _humanize_policy_label("capital_source") == "Capital Source"


def test_policy_help_explains_default_and_protected_roles() -> None:
    assert "latest portfolio classification" in _role_help("SYSTEM_DEFAULT")
    assert "avoid using it as trading funding" in _role_help("PROTECTED_CORE")


def test_money_values_are_sortable_from_display_strings() -> None:
    assert _parse_money_value("1,250.50 USDC") == 1250.50
    assert _parse_money_value("not loaded") == 0.0
