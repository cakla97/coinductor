# Research Notes

Put optional research notes here, for example outputs from Binance AI Agent Skills.

Supported formats:

- `.md`
- `.txt`
- `.json`

Generated research prompts are written to `research/requests` when notes are missing
or stale. Run the generated request with Binance AI Agent Skills, then save the final
research output here in `research/notes`.

Example Markdown note:

```markdown
# Binance skills market scan

Source: Binance AI Agent Skills

- BTC market structure remains range-bound.
- SOL volume is rising but risk remains elevated.
- No token security red flags found for the checked assets.
```

Example JSON note:

```json
{
  "source": "binance-skills",
  "title": "BTC/ETH market scan",
  "summary": "BTC is range-bound; ETH relative strength is neutral."
}
```
