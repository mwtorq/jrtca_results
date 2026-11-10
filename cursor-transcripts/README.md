# cursor-transcripts

Durable agent session notes for `jrtca_results`.

Enforced by `.cursor/rules/cursor-transcripts.mdc` (`alwaysApply: true`). Any session that inherits from a chat using that rule must keep logging here.

## Layout

| Path | Purpose |
|------|---------|
| `YYYY-MM-DD_<slug>.md` | Human-readable session note |
| `sessions/<uuid>.md` | Optional per Cursor session id |
| `README.md` | This file |

## Related canon

- `_OCR_CLEANUP_CATALOG_HANDOFF.md` — defect classes / audit keys
- `_plan_a1_d17_handoff.md` — pipeline status A1–D17
