"""Coinductor desktop application layer."""

from trading_agent import __version__ as __version__

# The desktop app ships from the same tree as the engine, so it reports the same
# version. trading_agent/__init__.py is the single source; pyproject reads it too.
