from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
import json

from .models import PortfolioAnalysis, ResearchBundle, ResearchNote, ResearchRequest, ResearchStatus


class ResearchLoader:
    def __init__(self, config: dict):
        self.config = config

    def load(self) -> ResearchBundle:
        research_config = self.config.get("research", {})
        if not research_config.get("enabled", False):
            return ResearchBundle(enabled=False, notes=())

        notes_dir = Path(str(research_config.get("notes_dir", "research/notes")))
        if not notes_dir.exists():
            return ResearchBundle(enabled=True, notes=())

        max_notes = int(research_config.get("max_notes", 5))
        max_chars = int(research_config.get("max_chars_per_note", 3000))
        files = sorted(
            [
                path
                for path in notes_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}
            ],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        notes = tuple(self._read_note(path, max_chars) for path in files[:max_notes])
        return ResearchBundle(enabled=True, notes=notes)

    def status_and_request(self, portfolio: PortfolioAnalysis) -> ResearchStatus:
        research_config = self.config.get("research", {})
        if not research_config.get("enabled", False):
            return ResearchStatus(
                enabled=False,
                notes_count=0,
                is_fresh=False,
                latest_note_age_hours=None,
                request=None,
                summary="Research layer is disabled.",
            )

        notes_dir = Path(str(research_config.get("notes_dir", "research/notes")))
        latest_age = self._latest_note_age_hours(notes_dir)
        freshness_hours = Decimal(str(research_config.get("freshness_hours", 24)))
        notes_count = self._notes_count(notes_dir)
        is_fresh = latest_age is not None and latest_age <= freshness_hours
        request = None
        if research_config.get("generate_requests", True) and not is_fresh:
            request = self._write_request(portfolio)

        if is_fresh:
            summary = f"Research notes are fresh. Latest note age is {latest_age} hours."
        elif notes_count == 0:
            summary = "No research notes are available. A Binance skills research request was generated."
        else:
            summary = f"Research notes are stale. Latest note age is {latest_age} hours; freshness window is {freshness_hours} hours."
        return ResearchStatus(
            enabled=True,
            notes_count=notes_count,
            is_fresh=is_fresh,
            latest_note_age_hours=latest_age,
            request=request,
            summary=summary,
        )

    def _read_note(self, path: Path, max_chars: int) -> ResearchNote:
        raw = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".json":
            return self._read_json_note(path, raw, max_chars)
        return ResearchNote(
            source=path.name,
            title=path.stem,
            content=raw.strip()[:max_chars],
        )

    def _read_json_note(self, path: Path, raw: str, max_chars: int) -> ResearchNote:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return ResearchNote(source=path.name, title=path.stem, content=raw.strip()[:max_chars])
        title = str(data.get("title") or data.get("query") or path.stem)
        source = str(data.get("source") or path.name)
        content = data.get("content") or data.get("summary") or data
        if not isinstance(content, str):
            content = json.dumps(content, ensure_ascii=False, indent=2)
        return ResearchNote(source=source, title=title, content=content.strip()[:max_chars])

    def _latest_note_age_hours(self, notes_dir: Path) -> Decimal | None:
        files = self._note_files(notes_dir)
        if not files:
            return None
        latest = max(path.stat().st_mtime for path in files)
        age_seconds = datetime.now(timezone.utc).timestamp() - latest
        return (Decimal(str(age_seconds)) / Decimal("3600")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _notes_count(self, notes_dir: Path) -> int:
        return len(self._note_files(notes_dir))

    def _note_files(self, notes_dir: Path) -> list[Path]:
        if not notes_dir.exists():
            return []
        return [
            path
            for path in notes_dir.iterdir()
            if path.is_file() and path.suffix.lower() in {".md", ".txt", ".json"}
        ]

    def _write_request(self, portfolio: PortfolioAnalysis) -> ResearchRequest:
        research_config = self.config.get("research", {})
        requests_dir = Path(str(research_config.get("requests_dir", "research/requests")))
        requests_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        title = "Binance Skills Research Request"
        path = requests_dir / f"{timestamp}_binance_skills_research.md"
        content = self._request_content(title, portfolio)
        path.write_text(content, encoding="utf-8")
        return ResearchRequest(path=str(path), title=title, content=content)

    def _request_content(self, title: str, portfolio: PortfolioAnalysis) -> str:
        research_config = self.config.get("research", {})
        symbols = research_config.get("request_symbols", [])
        assets = research_config.get("request_assets", [])
        top_assets = "\n".join(
            f"- {asset.asset}: allocation {asset.allocation_pct}%, action {asset.rebalance_action}, target {asset.target_pct if asset.target_pct is not None else 'none'}%"
            for asset in portfolio.assets[:10]
        )
        return "\n".join(
            [
                f"# {title}",
                "",
                "Use Binance AI Agent Skills for research only. Do not place orders, do not redeem Earn products, and do not recommend leverage, futures, or margin.",
                "",
                "## Analyze Symbols",
                "",
                *[f"- {symbol}" for symbol in symbols],
                "",
                "## Analyze Portfolio Assets",
                "",
                *[f"- {asset}" for asset in assets],
                "",
                "## Current Portfolio Context",
                "",
                f"- Total value: {portfolio.total_value_usdt} USDT",
                f"- Liquid value: {portfolio.liquid_value_usdt} USDT",
                f"- Locked value: {portfolio.locked_value_usdt} USDT ({portfolio.locked_pct}%)",
                f"- Unpriced assets: {', '.join(portfolio.unpriced_assets) if portfolio.unpriced_assets else 'None'}",
                "",
                "## Top Portfolio Assets",
                "",
                top_assets or "- No valued assets available.",
                "",
                "## Research Focus",
                "",
                "- Market trend regime and volatility for BTC, ETH, BNB, SOL, and WLD.",
                "- Range suitability for Spot Grid on BTCUSDT and ETHUSDT.",
                "- Token-specific risks for SOL and WLD as possible capital sources.",
                "- WBETH versus ETH exposure notes, including staking/liquidity considerations.",
                "- Any major Binance market or token-risk warnings relevant to this portfolio.",
                "",
                "## Return Format",
                "",
                "Save the final output as Markdown or JSON into research/notes/.",
                "Include these sections:",
                "",
                "- concise market summary",
                "- per-asset notes",
                "- grid suitability notes",
                "- risks",
                "- watchlist for next run",
                "- any explicit caveats or missing data",
                "",
            ]
        )
