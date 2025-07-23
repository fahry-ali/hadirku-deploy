# Dockerfile untuk Railway dengan MediaPipe (lebih ringan dari dlib)
FROM python:3.11-slim

# Install system dependencies minimal untuk MediaPipe
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1-mesa-glx \
    libgoogle-glog0v5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first untuk better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p static/captures instance

# Expose port
EXPOSE 8080

# Environment variables
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run the application
CMD ["python", "app.py"]
