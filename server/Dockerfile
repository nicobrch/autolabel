# Use a specific Python version
FROM python:3.12

# Install uv
RUN pip install uv

# Set working directory
WORKDIR /app

# Copy dependency definition files
COPY pyproject.toml uv.lock requirements.txt ./

# Create virtual environment and sync dependencies
# This also makes the venv's python the default one for subsequent RUN commands
RUN uv venv .venv && . .venv/bin/activate && uv sync
ENV PATH="/app/.venv/bin:$PATH"

# Install wget and OpenCV dependencies
RUN apt-get update && apt-get install -y wget ffmpeg libgl1-mesa-glx

# Copy the rest of the server application source code
COPY . .

# Initialize the database
WORKDIR /app/src
RUN uv run db.py

# Expose the port the server runs on
EXPOSE 8000

# Run the server
CMD ["uv", "run", "main.py", "--host", "0.0.0.0"]
