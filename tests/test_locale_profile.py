from trading_agent.locale_profile import LOCALE_PROFILES, REQUIRED_TRANSLATION_KEYS, SUPPORTED_LOCALES, locale_profile


def test_supported_locale_profiles_are_complete() -> None:
    assert tuple(LOCALE_PROFILES) == SUPPORTED_LOCALES

    for profile in LOCALE_PROFILES.values():
        assert profile.locale in SUPPORTED_LOCALES
        assert profile.fiat_currency
        assert profile.funding_currency == "USDC"
        assert profile.default_starting_budget > 0
        assert set(REQUIRED_TRANSLATION_KEYS).issubset(profile.translations)


def test_unknown_locale_falls_back_to_english() -> None:
    profile = locale_profile("unknown")

    assert profile.locale == "en-US"
