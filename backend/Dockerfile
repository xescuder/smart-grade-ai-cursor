FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port (will be overridden by environment variable)
EXPOSE 8000

# Use environment variable for port
CMD uvicorn main:app --host 0.0.0.0 --port ${BACKEND_PORT:-8000}
