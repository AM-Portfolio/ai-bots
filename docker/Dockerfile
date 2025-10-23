# Multi-stage build for Python backend
FROM python:3.11-slim as backend

WORKDIR /app

# Install system dependencies (cached layer)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files first (better caching)
COPY requirements.txt .
COPY code-intelligence/requirements.txt ./code-intelligence-requirements.txt

# Install dependencies (cached if requirements haven't changed)
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r code-intelligence-requirements.txt

# Copy only necessary application code (excludes node_modules, .git, etc.)
COPY main.py .
COPY shared/ ./shared/
COPY db/ ./db/
COPY features/ ./features/
COPY interfaces/ ./interfaces/
COPY observability/ ./observability/
COPY orchestration/ ./orchestration/
COPY vector_db/ ./vector_db/
COPY code-intelligence/ ./code-intelligence/
COPY ui/ ./ui/
COPY .env* ./
COPY openapi.json .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "main.py"]
