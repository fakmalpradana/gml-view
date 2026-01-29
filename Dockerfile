# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp_models uploads

# Expose port 8080 (Cloud Run standard)
ENV PORT=8080
EXPOSE 8080

# Run the application
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 300 server:app
