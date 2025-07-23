FROM python:3.11-slim

# Install minimal dependencies untuk MediaPipe
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p static/captures instance

# Expose port
EXPOSE 8080

# Run command
CMD ["python", "app.py"]
