# PromptPilot: Project Status

**Current phase:** Phase 1 (scaffold and configuration), complete
**Next action:** Phase 2 (FastAPI app, config, SQLite models, AI provider, prompt modules)

## Environment (inspected)
| Item | Result |
|---|---|
| Python | 3.12.3 |
| Node.js / npm | 22.22.2 / 10.9.7 |
| git | 2.43.0 |
| Project directory | Empty at start, so nothing to preserve |
| Package install in build sandbox | **Blocked** (no network); dependencies must be installed on your machine |

## Gemini model decision
- Default `GEMINI_MODEL=gemini-3.1-flash-lite` (stable, listed as free-tier eligible).
- Sources: Google's pricing page and third-party summaries; free-tier eligibility and model lineup change often.
- **Unverified:** that this model works with *your* key. Run `python scripts/check_env.py` after setting the key; it lists the models your key can see.
- Models that appear in older tutorials (`gemini-2.0-*`, `gemini-2.5-*`) are deprecated or being restricted, so they are not used.

## Phases
| Phase | Status |
|---|---|
| 1. Environment, structure, config files | Complete |
| 2. FastAPI, config, DB models, AI provider, prompts | Not started |
| 3. PDF upload, chunking, embeddings, ChromaDB | Not started |
| 4. Document Q&A, Study, Research, Viva, validation | Not started |
| 5. Prompt comparison, evaluation, dashboard API, backend tests | Not started |
| 6-10. Frontend, integration, docs | Not started |

## Feature checklist
| Feature | Status |
|---|---|
| A. Document management | Not started |
| B. Study Mode | Not started |
| C. Research Mode | Not started |
| D. Viva Mode | Not started |
| E. Document Q&A (RAG) | Not started |
| F. Prompt Evaluation Dashboard | Not started |
| G. Prompt Engineering Lab | Not started |
| H. Dashboard | Not started |

## Files created in Phase 1
`.gitignore`, `.env.example`, `requirements.txt`, `scripts/check_env.py`, `PROJECT_STATUS.md`, and empty directories for `backend/{api,models,services,prompts,tests,data,uploads}`, `frontend/`, `docs/`.

## Tests executed
- `py_compile scripts/check_env.py`: passed.
- `python scripts/check_env.py`: ran and correctly reported missing packages, `.env`, and key. This is expected here because nothing is installed yet.
- No application tests exist yet.

## Known issues
- Dependencies are lower-bound ranges, not pinned. Freeze them after your first successful install.
- Build sandbox cannot install packages, so backend tests cannot run here until network access is enabled.
