# Airspace Viewer

Flask web app that renders OpenAir airspace files on a Leaflet map. The server parses a bundled example or an uploaded `.txt`/`.air`/`.openair` file with `openair-rs-py`, converts it to GeoJSON (or KML for export), and the browser fetches it from `/api/airspaces` and draws it color-coded by airspace class. Every push to `main` deploys to Fly.io.
Domain terms are in `GLOSSARY.md`; decisions and their trade-offs are in `docs/adr/`.

## Commands

```bash
uv sync  # install deps and dev tools into .venv
uv run lefthook install  # install the git hooks, once per clone
uv run python application.py  # dev server on http://localhost:8000
uv run pytest  # run all tests
uv run pytest tests/test_routes.py  # run one test file
uv run ruff check --fix .  # lint and autofix
uv run ruff format .  # format
uv run mypy  # type-check app, tests and application.py
git ls-files -z '*.py' '*.md' '*.toml' '*.yml' '*.yaml' '*.json' '*.html' '*.js' '*.css' | xargs -0 npx --yes cspell --no-progress --no-must-find-files --config cspell.json  # spell-check what CI checks
npx --yes cspell --no-progress --config cspell.json README.md  # spell-check one file
uv run rumdl check .  # lint Markdown (config in .rumdl.toml)
docker build -t airspace-viewer .  # build the production image
```

Use `uv`, not `pip`. `lefthook.yml` runs ruff, mypy, rumdl, cspell and a 5,000-token-per-file budget on staged files at pre-commit and pytest at pre-push; CI (`.github/workflows/ci.yml`) runs all but the token budget on Python 3.12 and 3.14 and smoke-tests the Docker image.

## Conventions

### Architecture

- **The active dataset lives only in `AirspaceService`.** Get it with `get_airspace_service()` (`app/services/airspace_service.py`); never instantiate the service or cache airspaces elsewhere.
- **One pipeline from file to map.** `openair.parse_file` → `convert_raw_airspace` (`app/model/openair_types.py`) → `convert_airspace_to_geojson` / `convert_airspace_to_kml` (`app/utils/`); arcs and circles become polygons only in `app/utils/arc_utils.py`.
- **Routes live in three blueprints.** Pages, upload, examples and the generated `config.js`/`airspace_colors.css` in `app/routes/main_routes.py`; JSON and KML in `app/routes/api_routes.py`; icons and manifest in `app/routes/static_routes.py`.

### Airspace classes

- **`display_class()` is the only place that maps an `AC` token to the class shown.** It lives in `app/model/openair_types.py`; colors, legend and labels are keyed on its output (`"Restricted"`, not `"R"`).
- **Don't pass `normalize_legacy_classes=True` to `openair`.** It fails whole real-world files; see `docs/adr/0001-map-legacy-classes-in-app.md`.
- **Colors live only in `app/utils/airspace_colors.py`.** It generates the Python, JS and CSS colors; never hard-code a class color in a template, stylesheet or script.

### Dependencies

- **Add Python dependencies with `uv add`** (dev tools: `uv add --dev`) and commit the updated `uv.lock`; CI fails when the lock is stale.
- **Frontend libraries come from CDNs with SRI hashes.** They are pinned in `app/templates/_html_head.html` and `app/templates/index.html`; change the `integrity` hash together with the version.

### Tests and checks

- **`tests/conftest.py` resets the service singleton around every test.** Build the app with the `app`/`client` fixtures there; put OpenAir test inputs in `tests/fixtures/`.
- **Add correct words cspell doesn't know to `cspell-dictionary.txt`.**

## Hard constraints

- **Never push to `main` directly.** Every push to `main` deploys to production (`.github/workflows/fly-deploy.yml`); changes go through a pull request so CI runs first.
- **Never commit secrets.** `FLASK_SECRET_KEY` lives in Fly secrets and `FLY_API_TOKEN` in GitHub secrets; the env vars are listed in `.env.example`.

## Gotchas

- **The dataset is global and in-process.** An upload replaces the map for every visitor, and a second machine or gunicorn worker would serve a different dataset, so production runs one of each.
- **`openair-rs-py` >= 0.2 returns the raw `AC` token as `class`.** Read classes through `display_class()`, never from the raw dict.
- **Code must run on Python 3.12.** That is the `requires-python` floor CI tests, even though `.python-version` and the Docker image use 3.14.
- **`app/templates/js/config.js` and `app/templates/css/airspace_colors.css` are Jinja templates.** Routes render them; they are not files under `app/static/`.
- **Startup logs fake debug, info, warning and error lines.** `application.py` emits them on purpose; they don't mean anything failed.

## Docs

- `README.md` — what the project is and the quickstart.
- `docs/setup.md` — local setup, checks, Docker and troubleshooting.
- `docs/deployment.md` — Fly.io deploys, secrets and scaling.
- `.env.example` — every env var, annotated.
- `GLOSSARY.md` — OpenAir and airspace terms; read before naming anything class- or type-related.
- `docs/adr/` — why the code deviates from the obvious path.
