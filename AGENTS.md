# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Flask web app that renders OpenAir airspace files on a Leaflet map. Users pick a bundled example or upload a `.txt`/`.air`/`.openair` file; the server parses it, converts it to GeoJSON (or KML for export) and the browser draws it color-coded by airspace class. Deployed to Fly.io on every push to `main`.

## Commands

Uses [uv](https://docs.astral.sh/uv/) for dependency management; run everything through `uv run`. `requires-python` is `>=3.12`; `.python-version` and the Docker image use 3.14.

```bash
uv sync                              # install deps + dev tools, creates .venv
uv run lefthook install              # install git hooks (once per clone)
uv run python application.py         # dev server on http://localhost:8000

uv run pytest                        # full test suite
uv run pytest tests/test_routes.py   # single file

uv run ruff check --fix .            # lint + autofix
uv run ruff format .                 # format
uv run mypy                          # type-check (config in pyproject.toml)
npx cspell --config cspell.json "app/**"   # spell-check
```

`ruff`, `mypy` and `cspell` run on staged files at **pre-commit**; `pytest` runs at **pre-push** (see `lefthook.yml`). CI (`.github/workflows/ci.yml`) runs all of them on Python 3.12 and 3.14 plus `docker build`.

## Architecture

Flask app factory in `app/__init__.py`; `application.py` is the WSGI entry point (`gunicorn application:application` in the Dockerfile). Blueprints in `app/routes/`: `main_routes.py` (page, upload, examples, generated `config.js`/`airspace_colors.css`), `api_routes.py` (`/api/airspaces` GeoJSON, `/api/stats`, `/api/export_kml`), `static_routes.py` (icons, manifest).

`AirspaceService` (`app/services/airspace_service.py`) is a **module-global singleton** (`get_airspace_service()`) holding the one active dataset. Pipeline: `openair.parse_file` (the `openair-rs-py` package) → raw dicts → `convert_raw_airspace` → typed `Airspace` objects (`app/model/openair_types.py`) → `convert_airspace_to_geojson` / `convert_airspace_to_kml` (`app/utils/`, arcs and circles expanded to polygons by `arc_utils.py`).

**Airspace classes.** `openair-rs-py` >= 0.2 returns the raw `AC` token as `class` (`"R"`, `"Q"`, `"CTR"`, `"FFVL"`, ...). `display_class()` in `app/model/openair_types.py` maps legacy tokens back to the names 0.1.x returned (`"R"` -> `"Restricted"`), which is what colors, legend and labels are keyed on, and derives the class of an OpenAir v2 `AC UNC` airspace from its `AY` type. Unknown tokens are shown as-is in the default color. `normalize_legacy_classes=True` is deliberately not used: it raises (failing the whole file) when a legacy `AC` token disagrees with an existing `AY`, which real French files do thousands of times. Colors live in `app/utils/airspace_colors.py`, the single source for Python, the generated JS and the generated CSS.

## Conventions

- Ruff enforces `E`, `W`, `F`, `I` (isort) and `D` (Google-style docstrings); tests are exempt from `D`.
- Add dependencies with `uv add` (dev tools: `uv add --dev`); `uv.lock` is committed and CI checks it is current.
- Frontend libraries are loaded from CDNs in `app/templates/` with SRI hashes; update the hash with the version.
- Add unknown-but-correct words to `cspell-dictionary.txt`.
- `tests/conftest.py` resets the airspace singleton around every test.
