FROM python:3.11-slim

WORKDIR /app

# Install curl and other essential tools
RUN apt-get update && apt-get install -y curl wget && rm -rf /var/lib/apt/lists/*

# Install UV package manager
RUN curl -sSf https://astral.sh/uv/install.sh | sh

# Add UV to PATH
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy requirements
COPY requirements.txt .

# Install dependencies using UV
RUN uv pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p checkpoints configs data

# Download SAM2 model checkpoints
WORKDIR /app/checkpoints
RUN chmod +x download.sh && ./download.sh

# Ensure config files exist
WORKDIR /app/configs
RUN echo "Ensuring config files exist" && \
    touch sam2.1_hiera_t.yaml sam2.1_hiera_s.yaml sam2.1_hiera_b+.yaml sam2.1_hiera_l.yaml

# Initialize database using UV
WORKDIR /app
RUN uv run src/db.py

# Expose port
EXPOSE 8000

# Run the server using UV
CMD ["uv", "run", "src/main.py"]
