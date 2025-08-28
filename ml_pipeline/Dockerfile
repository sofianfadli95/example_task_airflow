FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the ML pipeline code
COPY train.py .
COPY predict.py .
COPY validate.py .

# Create necessary directories
RUN mkdir -p /app/models /app/predictions /app/data

# Make scripts executable
RUN chmod +x train.py predict.py validate.py

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Default command (can be overridden)
CMD ["python", "--help"]
