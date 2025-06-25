# Python Airspace Viewer

A Python-based interactive airspace visualization tool for viewing OpenAir airspace files. This project is inspired by [airspace-visualizer](https://github.com/dbrgn/airspace-visualizer) and partially migrated from TypeScript to Python.

## Features

- **Interactive Map**: Leaflet-based map with color-coded airspace display
- **File Support**: Drag & drop or upload `.txt`, `.air`, `.openair` files
- **Airspace Types**: Supports all common airspace classes (A, B, C, D, E, CTR, Restricted, etc.)
- **Real-time Visualization**: Immediate display of uploaded airspace data
- **Responsive UI**: Modern Bootstrap-based interface

## Quick Start

```bash
cd airspace-viewer
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python app.py
```

Open your browser and navigate to the displayed URL. The app loads with Switzerland airspace data by default.

## Architecture

- **Backend**: Flask web server with OpenAir file parsing
- **Frontend**: Leaflet maps with Bootstrap UI
- **Processing**: Server-side GeoJSON conversion vs original client-side WASM

## Usage

### Loading Airspace Data

1. **Default**: Loads Switzerland.txt automatically on startup
2. **Upload**: Use the file upload form or drag & drop files onto the map
3. **Reset**: Return to default Switzerland data

### API Endpoints

- `/`: Main application interface
- `/api/airspaces`: GeoJSON airspace data
- `/upload`: File upload handler

## Dependencies

- **Python**: `flask`, `openair`, `werkzeug`
- **Frontend**: `leaflet`, `bootstrap`
