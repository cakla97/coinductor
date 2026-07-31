"""Adding a listing to the tradeable list - the one step, and its guards.

There is no buy button on a listing. This is the whole of what the listing card
can do, so what it refuses matters as much as what it allows.
"""

from pathlib import Path

from coinductor.allowed_symbols import (
    MAX_SYMBOLS,
    add_allowed_symbol,
    is_valid_symbol,
    read_allowed_symbols,
    remove_allowed_symbol,
)

CONFIG = """\
# Comments here must survive: they are worth more than a tidy dump.
[strategy]
# Only these pairs are ever considered.
allowed_symbols = ["BTCUSDC", "ETHUSDC"]
max_positions = 2

[testnet_execution]
allowed_symbols = ["BTCUSDT"]
"""


def _config(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(CONFIG, encoding="utf-8")
    return path


def test_the_current_list_is_read(tmp_path) -> None:
    assert read_allowed_symbols(_config(tmp_path)) == ["BTCUSDC", "ETHUSDC"]


def test_a_missing_config_reads_as_empty(tmp_path) -> None:
    assert read_allowed_symbols(tmp_path / "absent.toml") == []


def test_adding_a_symbol_keeps_the_comments_and_the_other_section(tmp_path) -> None:
    path = _config(tmp_path)

    changed, reason = add_allowed_symbol(path, "newusdc")

    assert changed is True
    assert reason == "allowed_symbol_added"
    assert read_allowed_symbols(path) == ["BTCUSDC", "ETHUSDC", "NEWUSDC"]
    written = path.read_text(encoding="utf-8")
    assert "# Only these pairs are ever considered." in written
    assert "max_positions = 2" in written
    # The testnet section has a key of the same name and must not move.
    assert 'allowed_symbols = ["BTCUSDT"]' in written


def test_a_symbol_already_present_is_not_added_twice(tmp_path) -> None:
    path = _config(tmp_path)

    changed, reason = add_allowed_symbol(path, "BTCUSDC")

    assert changed is False
    assert reason == "allowed_symbol_already_there"
    assert read_allowed_symbols(path) == ["BTCUSDC", "ETHUSDC"]


def test_nonsense_is_refused_rather_than_written(tmp_path) -> None:
    path = _config(tmp_path)

    for bad in ("", "   ", "BTC USDC", "btc-usdc", "AB", "'; drop table runs;--", "X" * 40):
        changed, reason = add_allowed_symbol(path, bad)
        assert changed is False, f"{bad!r} was accepted"
        assert reason == "allowed_symbol_invalid"

    assert read_allowed_symbols(path) == ["BTCUSDC", "ETHUSDC"]


def test_the_list_cannot_grow_without_limit(tmp_path) -> None:
    """Otherwise it becomes a place things are added and never removed."""
    path = tmp_path / "config.toml"
    full = ", ".join(f'"SYM{index}USDC"' for index in range(MAX_SYMBOLS))
    path.write_text(f"[strategy]\nallowed_symbols = [{full}]\n", encoding="utf-8")

    changed, reason = add_allowed_symbol(path, "ONEMOREUSDC")

    assert changed is False
    assert reason == "allowed_symbol_list_full"


def test_a_missing_config_is_reported_rather_than_created(tmp_path) -> None:
    path = tmp_path / "absent.toml"

    changed, reason = add_allowed_symbol(path, "NEWUSDC")

    assert changed is False
    assert reason == "allowed_symbol_no_config"
    assert not path.exists()


def test_a_config_without_the_key_is_reported_not_guessed_at(tmp_path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[strategy]\nmax_positions = 2\n", encoding="utf-8")

    changed, reason = add_allowed_symbol(path, "NEWUSDC")

    assert changed is False
    assert reason == "allowed_symbol_not_written"


def test_what_can_be_added_can_be_removed(tmp_path) -> None:
    path = _config(tmp_path)
    add_allowed_symbol(path, "NEWUSDC")

    assert remove_allowed_symbol(path, "newusdc") is True
    assert read_allowed_symbols(path) == ["BTCUSDC", "ETHUSDC"]
    assert remove_allowed_symbol(path, "NOTTHERE") is False


def test_symbol_shape_is_checked_but_existence_is_not() -> None:
    """Whether Binance lists it is the exchange's answer, given at analysis."""
    assert is_valid_symbol("NEWUSDC") is True
    assert is_valid_symbol("newusdc") is True
    assert is_valid_symbol("BTC/USDC") is False
    assert is_valid_symbol("") is False
