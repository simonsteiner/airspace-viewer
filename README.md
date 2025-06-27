# Python Airspace Viewer

A Python-based interactive airspace visualization tool for viewing OpenAir airspace files. This project is inspired by [airspace-visualizer](https://github.com/dbrgn/airspace-visualizer) and partially migrated from TypeScript to Python.

## Features

- **Interactive Map**: Leaflet-based map with color-coded airspace display
- **File Support**: Drag & drop or upload `.txt`, `.air`, `.openair` files
- **Airspace Types**: Supports all common airspace classes (A, B, C, D, E, CTR, Restricted, etc.)
- **Real-time Visualization**: Immediate display of uploaded airspace data
- **Responsive UI**: Modern Bootstrap-based interface

## Quick Start

### Prerequisites

- Python 3.8 or higher

### Installation and Setup

```bash
# Clone and navigate to the project directory
cd airspace-viewer

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
# Install the package in development mode
pip install -e .
```

### Running the Application

```bash
python application.py
```

## Architecture

- **Backend**: Flask web server with OpenAir file parsing
- **Frontend**: Leaflet maps with Bootstrap UI
- **Data**: Server-side GeoJSON conversion for airspace visualization

## Usage

### Loading Airspace Data

1. **Default**: Loads `examples/Switzerland.txt` automatically on startup
2. **Upload**: Use the file upload form or drag & drop files onto the map
3. **Reset**: Return to default `examples/Switzerland.txt` data

### API Endpoints

- `/`: Main application interface
- `/api/airspaces`: GeoJSON airspace data
- `/upload`: File upload handler

## Development vs Production

- **Development**: Use `pip install -e .` for editable installation with local changes
- **Production**: Use `pip freeze > requirements.txt` to lock dependency versions for deployment

## Dependencies

- **Python**: `flask`, `openair`, `werkzeug`
- **Frontend**: `leaflet`, `bootstrap`

## Deployment

### Fly.io

This application can be deployed to [Fly.io](https://fly.io/) for production hosting.

#### Setup Requirements

Install the Fly.io CLI:

```bash
curl -L https://fly.io/install.sh | sh
# Add Fly.io to your PATH (add to `.bashrc` or `.zshrc`):
export FLYCTL_INSTALL="/home/$USER$/.fly"
export PATH="$FLYCTL_INSTALL/bin:$PATH"
```

#### Deployment Setup

The project includes a `fly.toml` configuration file for Fly.io deployment. To deploy:

```bash
# Login to Fly.io
fly auth login
# Launch the application (--ha=false ensures single machine deployment)
fly launch --ha=false
# If you already have two machines deployed, scale down to one
fly scale count 1
# Set Flask secret key for security
python3 -c "import secrets; print('FLASK_SECRET_KEY=' + secrets.token_hex(32))"
# Copy the output and set it as a secret (replace with actual generated key)
fly secrets set FLASK_SECRET_KEY=your_generated_key_here
# Deploy updates
fly deploy
```

#### Local Docker Testing

Before deploying to Fly.io, you can test the Docker image locally:

```bash
# Build the Docker image
docker build -t my-fly-app .

# Run the container locally on port 8080
docker run -p 8080:8080 my-fly-app
```

The application will be available at <http://localhost:8080>.

#### Application Details

- **App Name**: `airspace-viewer`
- **Admin URL**: <https://fly.io/apps/airspace-viewer>
- **Live URL**: <https://airspace-viewer.fly.dev>

#### CI/CD Setup

For automated deployments via GitHub Actions, create a deploy token:

```bash
fly tokens create deploy -x 999999h
```

Set the generated token as `FLY_API_TOKEN` secret in your GitHub repository settings.
