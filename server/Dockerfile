FROM python:3.12-slim

WORKDIR /app

# Install curl for downloading models
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p checkpoints data

# Download SAM2 model checkpoints
WORKDIR /app/checkpoints
RUN chmod +x download.sh && ./download.sh

# Initialize database
WORKDIR /app/src
RUN python db.py

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "main.py"]
