# Use Python 3.12 slim as the base image
FROM python:3.12-slim

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy Python dependency files and install
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Copy frontend dependency files and install
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm install

# Copy the entire project
COPY . .

# Ensure the public directory exists and has a placeholder data.json
RUN mkdir -p frontend/public && touch frontend/public/data.json

# Build the frontend (static generation)
RUN cd frontend && npm run build

# Make the entrypoint script executable
RUN chmod +x scripts/dokploy-entrypoint.sh

# Expose the port Nuxt will run on
EXPOSE 3000

# Use the entrypoint script to run the scraper and start the server
ENTRYPOINT ["/bin/bash", "scripts/dokploy-entrypoint.sh"]
