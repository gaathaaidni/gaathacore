# ADR 0001: Active FastAPI Runtime

- **Status:** Accepted transition decision
- **Context:** The repository contains FastAPI code and a legacy Flask blueprint/dependency surface.
- **Decision:** Treat `backend/app/main.py` as the active runtime and `backend/main.py` as its compatibility export. Treat unregistered Flask modules as legacy until explicitly mounted and tested.
- **Alternatives:** Continue treating both stacks as equivalent; remove legacy modules immediately.
- **Consequences:** Runtime tracing is clearer, but consolidation and duplicate behavior remain work items.
