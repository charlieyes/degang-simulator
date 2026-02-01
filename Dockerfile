FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip cache purge && \
    rm -rf /root/.cache/pip /tmp/*

# Copy application code (exclude large files via .dockerignore)
COPY . .

# Expose port (PORT will be set at runtime by Koyeb)
EXPOSE 8000

# Start application using PORT environment variable
# Use shell form (sh -c) to ensure environment variable expansion
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"
