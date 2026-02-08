# Backend Dockerfile for Polaris (Book Generator)
# Deploy as a Railway service with root directory set to /

FROM python:3.11-slim

# Install WeasyPrint system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libffi-dev \
    libcairo2 \
    libglib2.0-0 \
    libpangoft2-1.0-0 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directories for SQLite DB and generated book output
RUN mkdir -p data output

ENV PORT=8001

EXPOSE ${PORT}

CMD uvicorn book_generator.api_server:app --host 0.0.0.0 --port ${PORT}
