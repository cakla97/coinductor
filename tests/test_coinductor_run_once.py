"""The headless entry point the scheduled task calls.

The shipped build is one windowed executable, so the task runs that same binary
with --run-once rather than a second entry point that would have to be bundled,
signed and kept in step.
"""

import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATE = REPO / "config.example.toml"


def _run(tmp_path: Path, body: str) -> subprocess.CompletedProcess:
    """A fresh interpreter: importing Qt is what we are measuring."""
    shutil.copy(TEMPLATE, tmp_path / "config.toml")
    script = textwrap.dedent(
        f"""
        import sys
        sys.path.insert(0, r"{REPO}")
        {body}
        """
    )
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=300,
    )


# Every test stubs the analysis. A real one needs live Binance credentials, so
# a test that ran it would either be skipped everywhere or reach the network -
# and what is under test here is the entry point, not the engine.
_STUB = """
        import coinductor.application as application

        class Result:
            run_id = 7
            status = "OK"
            decision = "HOLD"

        class Stub:
            def run_analysis(self, options, progress=None):
                print("MODE", options.data_mode, "AI", options.ai_summary)
                return Result()

        application.CoinductorApplication = Stub
"""


def test_a_scheduled_run_reports_what_it_did(tmp_path) -> None:
    result = _run(
        tmp_path,
        _STUB + """
        from coinductor.desktop import run_once
        print("EXIT", run_once())
        """,
    )

    assert "EXIT 0" in result.stdout, result.stdout + result.stderr
    assert "Run 7 finished: OK - HOLD" in result.stdout


def test_a_scheduled_run_asks_for_real_data_and_never_for_proposals(tmp_path) -> None:
    """Unattended runs should ask for as little as they can, and AI proposals
    are the one option that puts model output into the decision path."""
    result = _run(
        tmp_path,
        _STUB + """
        import coinductor.application as application
        seen = {}
        original = application.CoinductorApplication

        class Capture(original):
            def run_analysis(self, options, progress=None):
                seen.update(vars(options))
                return super().run_analysis(options, progress)

        application.CoinductorApplication = Capture
        from coinductor.desktop import run_once
        run_once()
        print("PROPOSALS", seen["ai_proposals"])
        print("SUBMIT", seen.get("live_submit"), seen.get("live_confirm"))
        """,
    )

    assert "MODE REAL" in result.stdout, result.stdout + result.stderr
    assert "PROPOSALS False" in result.stdout
    # No confirmation string exists to pass, so nothing can be submitted.
    assert "SUBMIT False " in result.stdout


def test_a_scheduled_run_never_loads_a_gui_toolkit(tmp_path) -> None:
    """It has no window, no display, and on a headless session importing Qt
    is not merely wasteful - it can fail outright."""
    result = _run(
        tmp_path,
        _STUB + """
        from coinductor.desktop import run_once
        run_once()
        qt = [m for m in sys.modules if m.startswith("PySide6")]
        print("QT", len(qt))
        """,
    )

    assert "QT 0" in result.stdout, f"Qt was imported: {result.stdout}"


def test_the_flag_is_what_selects_it(tmp_path) -> None:
    """main() must dispatch on --run-once before touching Qt at all."""
    result = _run(
        tmp_path,
        _STUB + """
        from coinductor import desktop
        sys.argv = ["coinductor", "--run-once"]
        code = desktop.main()
        print("EXIT", code)
        print("QT", len([m for m in sys.modules if m.startswith("PySide6")]))
        """,
    )

    assert "EXIT 0" in result.stdout, result.stdout + result.stderr
    assert "QT 0" in result.stdout


def test_a_failing_run_reports_rather_than_crashing(tmp_path) -> None:
    """A scheduled task that raises leaves a stack trace nobody will read."""
    result = _run(
        tmp_path,
        """
        import coinductor.desktop as desktop

        class Boom:
            def run_analysis(self, *a, **k):
                raise RuntimeError("exchange unreachable")

        import coinductor.application as application
        application.CoinductorApplication = Boom
        print("EXIT", desktop.run_once())
        """,
    )

    assert "EXIT 1" in result.stdout, result.stdout + result.stderr
    assert "exchange unreachable" in result.stdout
