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
cd app
python app.py
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
