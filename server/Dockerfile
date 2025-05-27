FROM python:3.10-slim

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
RUN mkdir -p checkpoints configs data

# Download SAM2 model checkpoints
WORKDIR /app/checkpoints
RUN chmod +x download.sh && ./download.sh

# Download or create SAM2 config files if needed
WORKDIR /app/configs
RUN echo "Ensuring config files exist" && \
    touch sam2.1_hiera_t.yaml sam2.1_hiera_s.yaml sam2.1_hiera_b+.yaml sam2.1_hiera_l.yaml

# Initialize database
WORKDIR /app/src
RUN python db.py

# Expose port
EXPOSE 8000

# Run the server
CMD ["python", "main.py"]
