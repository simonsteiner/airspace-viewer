# Local setup

## Prerequisites

- Python 3.12 or newer. `.python-version` and the Docker image use 3.14; CI tests 3.12 and 3.14.
- [uv](https://docs.astral.sh/uv/) for dependencies and running tools.
- Node.js, for `npx cspell` (the spell-check hook).
- Docker, only to build the production image locally.

## Install

```bash
uv sync                    # create .venv, install the app and dev tools from uv.lock
uv run lefthook install    # install the git hooks (once per clone)
```

Add a dependency with `uv add <package>` (a dev tool with `uv add --dev <package>`); both update `uv.lock`, which is committed.

## Run

```bash
uv run python application.py   # dev server on http://localhost:8000
```

The server loads `app/examples/Switzerland.txt` on startup. Uploads are limited to 16 MB and to the `.txt`, `.air` and `.openair` extensions (`app/config.py`).

## Configuration

Environment variables are listed in [`.env.example`](../.env.example). Nothing loads a `.env` file automatically; export the variables in your shell. Locally none are required.

## Checks

```bash
uv run pytest                  # test suite
uv run ruff check --fix .      # lint (pycodestyle, pyflakes, isort, Google-style docstrings)
uv run ruff format .           # format
uv run mypy                    # type-check (config in pyproject.toml)
git ls-files -z '*.py' '*.md' '*.toml' '*.yml' '*.yaml' '*.json' '*.html' '*.js' '*.css' \
  | xargs -0 npx --yes cspell --no-progress --no-must-find-files --config cspell.json   # spell-check, as CI runs it
uv run rumdl check .           # Markdown lint (config in .rumdl.toml)
```

[lefthook](https://github.com/evilmartians/lefthook) runs ruff, mypy, rumdl (Markdown) and cspell on staged files at pre-commit and pytest at pre-push (see `lefthook.yml`).

Pre-commit also blocks any staged file over 5,000 tokens (bytes / 4) and prints how to split it (`scripts/hooks/check-file-tokens.py`). It skips lockfiles, binaries and anything `.gitattributes` marks `linguist-generated` or `linguist-vendored`, such as the OpenAir files in `app/examples/`; CI doesn't run this check. To skip the hooks once in an emergency, run `LEFTHOOK=0 git commit …`.

CI (`.github/workflows/ci.yml`) runs the same checks on every pull request and push to `main`, on Python 3.12 and 3.14, checks that `uv.lock` is current, and builds and smoke-tests the Docker image.

## Docker

```bash
docker build -t airspace-viewer .
docker run -p 8080:8080 airspace-viewer   # http://localhost:8080, health check at /health
```

The image runs `gunicorn application:application` on port 8080 with the production config.

## Troubleshooting

- **Startup prints error and warning lines.** `application.py` logs one sample line per log level at startup; they don't indicate a failure.
- **cspell flags a correct word.** Add it to `cspell-dictionary.txt`.
- **CI fails on `uv lock --check`.** You edited `pyproject.toml` by hand; run `uv lock` and commit `uv.lock`.
