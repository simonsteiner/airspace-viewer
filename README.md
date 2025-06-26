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
- **Processing**: Server-side GeoJSON conversion vs original client-side WASM

## Usage

### Loading Airspace Data

1. **Default**: Loads `examples/Switzerland.txt` automatically on startup
2. **Upload**: Use the file upload form or drag & drop files onto the map
3. **Reset**: Return to default `examples/Switzerland.txt` data

### API Endpoints

- `/`: Main application interface
- `/api/airspaces`: GeoJSON airspace data
- `/upload`: File upload handler

## Deployment

### AWS Elastic Beanstalk

The project includes GitHub Actions for automatic deployment to AWS Elastic Beanstalk. For manual deployment:

1. **Update requirements.txt for production**:

   ```bash
   # Activate your virtual environment
   source .venv/bin/activate
   
   # Generate production requirements
   pip freeze > requirements.txt
   ```

2. **Configure GitHub Secrets**: Set up the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

   - `AWS_ACCESS_KEY_ID`: AWS access key for deployment
   - `AWS_SECRET_ACCESS_KEY`: AWS secret access key for deployment
   - `AWS_REGION`: AWS region (e.g., `us-east-1`, `eu-west-1`)
   - `EB_APP_NAME`: Elastic Beanstalk application name
   - `EB_ENV_NAME`: Elastic Beanstalk environment name
   - `EB_S3_BUCKET`: S3 bucket for storing deployment artifacts
   - `FLASK_SECRET_KEY`: Secret key for Flask session security

3. **Deploy using GitHub Actions**: Push to the `main` branch to trigger automatic deployment

4. **Manual deployment**: Use the AWS CLI or Elastic Beanstalk console with the `application.py` WSGI entry point

### Development vs Production

- **Development**: Use `pip install -e .` for editable installation
- **Production**: Use `pip freeze > requirements.txt` to lock dependency versions for AWS deployment

The GitHub Actions workflow automatically:

- Installs dependencies from `requirements.txt`
- Creates a deployment package excluding development files
- Deploys to Elastic Beanstalk with environment variables

## Dependencies

- **Python**: `flask`, `openair`, `werkzeug`
- **Frontend**: `leaflet`, `bootstrap`
