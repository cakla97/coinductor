"""Telling someone a newer Coinductor exists, without nagging them about it.

The rule that shapes all of this: a false "you are out of date" is worse than
silence, so every case the code does not understand - an unparseable tag, no
network, a prerelease - reports nothing rather than guessing.
"""

from datetime import datetime, timedelta, UTC

import pytest

from coinductor.update_check import (
    CHECK_INTERVAL_HOURS,
    UpdateCheckService,
    is_newer,
    parse_version,
)


def _service(tmp_path, current="1.4.3") -> UpdateCheckService:
    return UpdateCheckService(path=tmp_path / "update_check.toml", current_version=current)


# -- version arithmetic -----------------------------------------------------


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1.4.3", (1, 4, 3)),
        ("v1.4.3", (1, 4, 3)),
        ("  v2.0.0  ", (2, 0, 0)),
        ("1.4", None),
        ("v1.4.3-rc1", None),
        ("latest", None),
        ("", None),
        (None, None),
    ],
)
def test_version_parsing(text, expected) -> None:
    assert parse_version(text) == expected


@pytest.mark.parametrize(
    "candidate,current,expected",
    [
        ("1.4.4", "1.4.3", True),
        ("1.5.0", "1.4.3", True),
        ("2.0.0", "1.4.3", True),
        ("1.4.3", "1.4.3", False),
        ("1.4.2", "1.4.3", False),
        ("1.10.0", "1.9.0", True),
    ],
)
def test_newer_compares_numbers_not_strings(candidate, current, expected) -> None:
    assert is_newer(candidate, current) is expected


def test_an_unreadable_version_is_never_newer() -> None:
    """Silence beats a wrong claim, in both directions."""
    assert is_newer("banana", "1.4.3") is False
    assert is_newer("1.4.4", "banana") is False


# -- what the screen is told ------------------------------------------------


def test_nothing_is_said_before_a_check_has_happened(tmp_path) -> None:
    assert _service(tmp_path).available() == ""


def test_a_newer_release_is_worth_mentioning(tmp_path) -> None:
    service = _service(tmp_path)

    service.record("v1.5.0")

    assert service.available() == "v1.5.0"


def test_the_running_version_is_not_an_update(tmp_path) -> None:
    service = _service(tmp_path)

    service.record("v1.4.3")

    assert service.available() == ""


def test_an_older_release_is_not_an_update(tmp_path) -> None:
    """A downgrade on the remote must never read as something to install."""
    service = _service(tmp_path)

    service.record("v1.4.2")

    assert service.available() == ""


def test_a_dismissed_version_stays_dismissed(tmp_path) -> None:
    service = _service(tmp_path)
    service.record("v1.5.0")

    service.dismiss()

    assert service.available() == ""


def test_a_later_release_speaks_up_again_after_a_dismissal(tmp_path) -> None:
    """Putting one version away is not agreeing to miss every later one."""
    service = _service(tmp_path)
    service.record("v1.5.0")
    service.dismiss()

    service.record("v1.6.0")

    assert service.available() == "v1.6.0"


def test_upgrading_ends_the_message_without_any_dismissal(tmp_path) -> None:
    service = _service(tmp_path)
    service.record("v1.5.0")

    upgraded = UpdateCheckService(path=service.path, current_version="1.5.0")

    assert upgraded.available() == ""


# -- how often it asks ------------------------------------------------------


def test_the_first_run_is_always_due(tmp_path) -> None:
    assert _service(tmp_path).due() is True


def test_a_recent_check_is_not_repeated(tmp_path) -> None:
    service = _service(tmp_path)
    service.record("v1.4.3")

    assert service.due() is False


def test_a_day_later_it_asks_again(tmp_path) -> None:
    service = _service(tmp_path)
    now = datetime.now(UTC)
    service.record("v1.4.3", now=now)

    later = now + timedelta(hours=CHECK_INTERVAL_HOURS, minutes=1)

    assert service.due(now=later) is True


def test_an_unreadable_timestamp_asks_again(tmp_path) -> None:
    path = tmp_path / "update_check.toml"
    path.write_text('[updates]\nchecked_at = "not a date"\n', encoding="utf-8")

    assert UpdateCheckService(path=path).due() is True


def test_a_corrupt_record_is_not_fatal(tmp_path) -> None:
    path = tmp_path / "update_check.toml"
    path.write_text("this is not toml {{{", encoding="utf-8")

    service = UpdateCheckService(path=path, current_version="1.4.3")

    assert service.available() == ""
    assert service.due() is True


# -- the network call --------------------------------------------------------


def _fetch_returning(monkeypatch, payload, service):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            import json

            return json.dumps(payload).encode("utf-8")

    monkeypatch.setattr(
        "coinductor.update_check.urllib.request.urlopen",
        lambda request, timeout=None: FakeResponse(),
    )
    return service.fetch()


def test_a_published_release_returns_its_tag(tmp_path, monkeypatch) -> None:
    service = _service(tmp_path)

    assert _fetch_returning(monkeypatch, {"tag_name": "v1.5.0"}, service) == "v1.5.0"


def test_a_prerelease_is_not_offered(tmp_path, monkeypatch) -> None:
    service = _service(tmp_path)

    assert _fetch_returning(monkeypatch, {"tag_name": "v1.5.0", "prerelease": True}, service) == ""


def test_a_draft_is_not_offered(tmp_path, monkeypatch) -> None:
    service = _service(tmp_path)

    assert _fetch_returning(monkeypatch, {"tag_name": "v1.5.0", "draft": True}, service) == ""


def test_a_tag_that_will_not_parse_is_ignored(tmp_path, monkeypatch) -> None:
    service = _service(tmp_path)

    assert _fetch_returning(monkeypatch, {"tag_name": "nightly"}, service) == ""


def test_no_network_is_not_an_error(tmp_path, monkeypatch) -> None:
    """Offline is the normal state for this app; it must cost nothing."""
    import urllib.error

    def explode(request, timeout=None):
        raise urllib.error.URLError("no route to host")

    monkeypatch.setattr("coinductor.update_check.urllib.request.urlopen", explode)

    assert _service(tmp_path).fetch() == ""


# -- the switch in the config ------------------------------------------------

from coinductor.update_check import (  # noqa: E402
    DISABLE_ENV,
    apply_check_on_start,
    ensure_section,
    read_check_on_start,
)

MINIMAL_CONFIG = """\
[app]
mode = "DRY_RUN"
mock_data = true
base_currency = "USDC"
"""


def _config(tmp_path, body=MINIMAL_CONFIG):
    path = tmp_path / "config.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_a_config_without_the_section_still_checks(tmp_path, monkeypatch) -> None:
    """Absent means yes, so an upgrade does not silently stop reporting fixes."""
    monkeypatch.delenv(DISABLE_ENV, raising=False)

    assert read_check_on_start(_config(tmp_path)) is True


def test_the_offline_guard_wins_over_the_config(tmp_path, monkeypatch) -> None:
    """The suite is offline by contract; conftest sets this for every test."""
    monkeypatch.setenv(DISABLE_ENV, "1")

    assert read_check_on_start(_config(tmp_path)) is False


def test_the_section_is_added_to_an_older_config(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    path = _config(tmp_path)

    assert ensure_section(path) is True
    assert "[updates]" in path.read_text(encoding="utf-8")
    assert read_check_on_start(path) is True


def test_adding_the_section_twice_changes_nothing(tmp_path) -> None:
    path = _config(tmp_path)
    ensure_section(path)
    before = path.read_text(encoding="utf-8")

    assert ensure_section(path) is False
    assert path.read_text(encoding="utf-8") == before


def test_the_switch_can_be_turned_off_and_on(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    path = _config(tmp_path)

    apply_check_on_start(path, False)
    assert read_check_on_start(path) is False

    apply_check_on_start(path, True)
    assert read_check_on_start(path) is True


def test_turning_it_off_survives_a_config_that_never_had_the_section(tmp_path, monkeypatch) -> None:
    """`_apply` only edits keys that exist, so without ensure_section this
    reported success and changed nothing - in the direction someone cares about."""
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    path = _config(tmp_path)

    apply_check_on_start(path, False)

    assert read_check_on_start(path) is False


def test_the_rest_of_the_config_survives_the_write(tmp_path, monkeypatch) -> None:
    monkeypatch.delenv(DISABLE_ENV, raising=False)
    path = _config(tmp_path)

    apply_check_on_start(path, False)

    text = path.read_text(encoding="utf-8")
    assert "[app]" in text
    assert 'base_currency = "USDC"' in text
