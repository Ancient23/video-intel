# Base image with Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /services/backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path to the backend directory
ENV PYTHONPATH=/services/backend
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden in docker-compose)
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]