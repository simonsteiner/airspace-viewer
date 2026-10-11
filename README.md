# Python Airspace Viewer

An interactive viewer for OpenAir airspace files. Pick a bundled example or drop a `.txt`, `.air` or `.openair` file onto the page, and the airspaces are drawn on a Leaflet map, color-coded by class, with a legend, statistics and KML export. Inspired by [airspace-visualizer](https://github.com/dbrgn/airspace-visualizer) and partially migrated from TypeScript to Python.

Live at <https://airspace-viewer.fly.dev>.

## Quick start

Needs Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync                        # create .venv, install the app and dev tools
uv run python application.py   # http://localhost:8000
```

The app starts with `app/examples/Switzerland.txt` loaded; **Reset** returns to it.

## Docs

- [docs/setup.md](docs/setup.md) — local setup, checks, Docker and troubleshooting
- [docs/deployment.md](docs/deployment.md) — deploying to Fly.io
- [.env.example](.env.example) — environment variables
- [GLOSSARY.md](GLOSSARY.md) — OpenAir and airspace terms
- [docs/adr/](docs/adr/) — design decisions
- [AGENTS.md](AGENTS.md) — rules for changing the code (for people and coding agents)
