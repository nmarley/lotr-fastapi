# FastAPI Boilerplate Service

This is a simple FastAPI service boilerplate.

## Installation

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Running the Service

Run the FastAPI development server:

```bash
uvicorn main:app --reload
```

The service will be available at http://127.0.0.1:8000.

The health check endpoint is available at http://127.0.0.1:8000/health.

## Running with Docker

Build and run the service using Docker Compose:

```bash
docker compose up --build
```

The service will be available at http://127.0.0.1:8000.

The health check endpoint is available at http://127.0.0.1:8000/health.

To stop the service, press `Ctrl+C` and then run:

```bash
docker compose down
```

## Running Tests

Run the tests using pytest:

```bash
.venv/bin/pytest
```