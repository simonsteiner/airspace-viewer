# Deployment

The app runs on [Fly.io](https://fly.io/) as the `airspace-viewer` app (`fly.toml`).

- Live: <https://airspace-viewer.fly.dev>
- Dashboard: <https://fly.io/apps/airspace-viewer>

## Release flow

Every push to `main` deploys: `.github/workflows/fly-deploy.yml` runs `flyctl deploy --remote-only`, which builds the `Dockerfile` on Fly's builders. Merge through a pull request so CI (`.github/workflows/ci.yml`) has run first.

## Secrets

- **`FLASK_SECRET_KEY`** — Fly secret, signs the Flask session (flash messages). Without it the app falls back to a hard-coded development key.
- **`FLY_API_TOKEN`** — GitHub repository secret, used by the deploy workflow.

Never put secret values in the repo; `.env.example` lists the variables without values.

## Scaling

Run exactly one machine. The loaded airspace dataset lives in process memory (`AirspaceService`), so a second machine would serve whatever file was last loaded there. The image runs gunicorn with its default single worker for the same reason.

`fly.toml` lets Fly stop the machine when idle (`min_machines_running = 0`) and start it on the next request; the first request after a stop is slow and shows the default dataset.

## Manual setup

Install the Fly CLI:

```bash
curl -L https://fly.io/install.sh | sh
export FLYCTL_INSTALL="$HOME/.fly"          # add both lines to .bashrc or .zshrc
export PATH="$FLYCTL_INSTALL/bin:$PATH"
```

Create the app and its secret:

```bash
fly auth login
fly launch --ha=false                       # single machine
fly scale count 1                           # if two machines were created anyway
fly secrets set FLASK_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
fly deploy                                  # deploy by hand
```

Create the token for the deploy workflow and store it as the `FLY_API_TOKEN` secret in the GitHub repository settings:

```bash
fly tokens create deploy -x 999999h
```

To try the production image locally first, see [setup.md](setup.md#docker).
