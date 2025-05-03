FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY pyproject.toml /app/
COPY README.md /app/

# Install the package
RUN pip install --no-cache-dir -e .

# Copy the rest of the application
COPY . /app/

# Initialize the database
RUN mkdir -p /app/storage
RUN codegen-oss init

# Expose the API port
EXPOSE 8000

# Run the API server
CMD ["codegen-oss", "server"]

