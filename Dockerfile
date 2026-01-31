FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for TTS (ffmpeg, etc.)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (PORT will be set at runtime by Koyeb)
EXPOSE 8000

# Start application using PORT environment variable
# Use shell form (sh -c) to ensure environment variable expansion
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
