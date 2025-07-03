# 🚀 AutoLabel Project

AutoLabel is a tool for automated video labeling using Segment Anything Model 2 (SAM2). The project consists of a React frontend client and a FastAPI backend server.

## Features

- Upload and process videos for labeling
- Automated segmentation using SAM2
- Interactive labeling interface
- Metadata management with SQLite database

## Architecture

- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **ML Model**: SAM2 from Meta

## Quick Start with Docker

The easiest way to run the complete application is using Docker Compose:

```shell
# Download SAM2 Model Checkpoints
cd server/checkpoints
./download.sh

# Build and start all services
cd ../.. # Back to project root
docker-compose up -d
```

After starting the containers:

- Frontend: http://localhost:8080
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Development Setup

If you prefer to run the client and server separately for development:

### Client

See [client README](./client/README.md) for detailed instructions.

```shell
cd client
pnpm install
pnpm run build
pnpm run preview
```

### Server

See [server README](./server/README.md) for detailed instructions.

```shell
cd server
uv venv .venv
uv sync
cd checkpoints
./download.sh
cd ../src
uv run db.py
uv run main.py
```
