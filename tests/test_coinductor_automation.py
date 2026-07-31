"""Automation settings: read, clamp, write, and survive an old config.

The section did not exist before this feature, so every config in the wild is
missing it. _apply only edits keys already present, which means without the
append step the app would accept a schedule and quietly discard it.
"""

from pathlib import Path

from coinductor.automation import (
    DEFAULTS,
    MAX_INTERVAL_HOURS,
    MIN_INTERVAL_HOURS,
    apply_automation_to_config,
    clamp_interval,
    ensure_section,
    read_automation,
)

OLD_CONFIG = """\
# A config written before automation existed.
[app]
mode = "DRY_RUN"

[retention]
keep_database_runs = 500
"""

NEW_CONFIG = OLD_CONFIG + """
[automation]
enabled = true
interval_hours = 6
ai_summary = true
live_preview = false
"""


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_a_config_without_the_section_reads_as_off(tmp_path) -> None:
    """Fail closed: an upgrade must not start running analyses by itself."""
    settings = read_automation(_write(tmp_path, OLD_CONFIG))

    assert settings.enabled is False
    assert settings.interval_hours == DEFAULTS["interval_hours"]
    assert settings.ai_summary is False
    assert settings.live_preview is False


def test_a_missing_config_reads_as_off(tmp_path) -> None:
    assert read_automation(tmp_path / "absent.toml").enabled is False


def test_settings_are_read_back(tmp_path) -> None:
    settings = read_automation(_write(tmp_path, NEW_CONFIG))

    assert settings.enabled is True
    assert settings.interval_hours == 6
    assert settings.ai_summary is True
    assert settings.live_preview is False
    assert settings.interval_seconds == 6 * 3600


def test_the_interval_is_clamped_rather_than_refused() -> None:
    assert clamp_interval(6) == 6
    assert clamp_interval("6") == 6
    assert clamp_interval("6,5") == 6  # a Czech keyboard types a comma
    assert clamp_interval(0) == MIN_INTERVAL_HOURS
    assert clamp_interval(-5) == MIN_INTERVAL_HOURS
    assert clamp_interval(10_000) == MAX_INTERVAL_HOURS
    # Nothing readable at all keeps the shipped default rather than inventing one.
    assert clamp_interval("soon") == DEFAULTS["interval_hours"]
    assert clamp_interval(None) == DEFAULTS["interval_hours"]


def test_an_old_config_gains_the_section_and_keeps_everything_else(tmp_path) -> None:
    path = _write(tmp_path, OLD_CONFIG)

    assert ensure_section(path) is True

    written = path.read_text(encoding="utf-8")
    assert "# A config written before automation existed." in written
    assert "keep_database_runs = 500" in written
    assert "[automation]" in written
    # Appended with the shipped defaults, so it cannot turn itself on.
    assert read_automation(path).enabled is False


def test_the_section_is_appended_only_once(tmp_path) -> None:
    path = _write(tmp_path, OLD_CONFIG)

    assert ensure_section(path) is True
    assert ensure_section(path) is False
    assert path.read_text(encoding="utf-8").count("[automation]") == 1


def test_saving_into_an_old_config_actually_takes_effect(tmp_path) -> None:
    """The whole point of the append: this used to write nothing at all."""
    path = _write(tmp_path, OLD_CONFIG)

    changed = apply_automation_to_config(
        path, enabled=True, interval_hours=8, ai_summary=True, live_preview=False
    )

    assert changed, "nothing was written into a config that lacked the section"
    settings = read_automation(path)
    assert settings.enabled is True
    assert settings.interval_hours == 8
    assert settings.ai_summary is True


def test_saving_the_same_settings_twice_reports_no_change(tmp_path) -> None:
    """Told apart from a refusal, the way the order caps had to be."""
    path = _write(tmp_path, NEW_CONFIG)

    first = apply_automation_to_config(
        path, enabled=False, interval_hours=12, ai_summary=False, live_preview=True
    )
    second = apply_automation_to_config(
        path, enabled=False, interval_hours=12, ai_summary=False, live_preview=True
    )

    assert first
    assert second == {}


def test_an_out_of_range_interval_is_stored_clamped(tmp_path) -> None:
    path = _write(tmp_path, NEW_CONFIG)

    apply_automation_to_config(
        path, enabled=True, interval_hours=99_999, ai_summary=False, live_preview=False
    )

    assert read_automation(path).interval_hours == MAX_INTERVAL_HOURS


def test_a_missing_config_is_left_alone(tmp_path) -> None:
    path = tmp_path / "absent.toml"

    assert apply_automation_to_config(
        path, enabled=True, interval_hours=6, ai_summary=False, live_preview=False
    ) == {}
    assert not path.exists()
