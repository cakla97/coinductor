# Contributing

Thanks for looking. This is a small project with one maintainer, so the fastest way to be
useful is a clear bug report — ideally one that says what you did, what happened, and what
you expected instead.

## Reporting a bug

Open an issue with:

- the version (**Settings → About**, or the title bar of the installer),
- what you were doing,
- what happened,
- whether the app was connected to Binance or running on `mock_data = true`.

**Settings → Export diagnostics** writes a bundle that answers most of the environment
questions at once. It deliberately contains no keys, secrets, balances or holdings — but
read it before attaching it, because it does name your home directory.

**Never paste an API key, a secret, or a screenshot showing one.** If you think you have
exposed one, delete it in Binance first and worry about the issue afterwards.

For anything that looks like a security problem, see [SECURITY.md](SECURITY.md) instead of
opening a public issue.

## Working on the code

```bash
python -m pip install -e ".[desktop,dev]"
python -m pytest -q                                   # fully offline, no keys needed
python -m ruff check trading_agent coinductor tests
```

The suite runs without network access and without credentials. If a change of yours needs
either, that is worth a conversation before the code.

## Two rules that are not negotiable

**The LLM proposes; deterministic code decides.** `AiAnalyst` returns a candidate action and
nothing more. `RiskEngine.evaluate()` governs whether anything happens, and every execution
path is gated behind it. A change that lets model output reach a submit path will not be
merged, however it is framed.

**User-facing text is a message, not a sentence.** The engine emits a key plus its
parameters (`trading_agent/messages.py`) and the text is composed once per reader — English
for the Markdown report, the user's language for the app. An f-string assigned to a
user-facing field cannot be translated afterwards, and there is a test that rejects one.

`CLAUDE.md` has the rest of the working notes: what owns which file, and the handful of
things that will bite you.

## Pull requests

- One thing per pull request.
- Tests for behaviour that changed. If you are fixing a bug, a test that fails without your
  fix is worth more than three that pass either way.
- `pytest` and `ruff` clean.
- Say what you verified and how. "Ran the app and clicked it" is a fine answer; claiming a
  test covers something it does not is not.
