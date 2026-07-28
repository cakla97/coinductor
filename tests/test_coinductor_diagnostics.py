"""The diagnostics bundle: where it lands and what it must not contain."""

from coinductor.diagnostics_service import DiagnosticsService

def test_bundle_path_is_absolute(tmp_path, monkeypatch) -> None:
    """The path is reported to the user and used to open the file.

    A path relative to the working directory is unusable to someone running an
    installed build - they have no reason to know where that directory is, and
    a bundle written to "outputs/diagnostics" reads as if nothing happened.
    """
    monkeypatch.chdir(tmp_path)

    path = DiagnosticsService().write_bundle()

    assert path.is_absolute(), path
    assert path.exists()


def test_bundle_states_up_front_that_it_carries_no_secrets(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    text = DiagnosticsService().write_bundle().read_text(encoding="utf-8")

    assert "no API keys" in text.splitlines()[1]
