# Use Python 3.10 as the base image
FROM python:3.10-slim
# Set working directory
WORKDIR /app
# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app
# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements file
COPY requirements.txt .
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Copy the application code
COPY . .
# Create necessary directories
RUN mkdir -p data/reviews data/insights config
# Expose the port
EXPOSE 8000
# Set the entrypoint
ENTRYPOINT ["python", "-m", "pr_review_bot.app"]
# Set default command
CMD ["--host", "0.0.0.0", "--port", "8000"]
