###########################################
# Stage 1 — Build dependencies normally
###########################################
FROM python:3.12.3-slim-bookworm AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install everything normally (no wheel build)

RUN pip install --upgrade pip 
 
RUN pip install fastembed beautifulsoup4 \ 
 && pip install fastapi uvicorn\ 
 && pip install chromadb fastmcp python-multipart

###########################################
# Stage 2 — Lightweight runtime
###########################################
FROM python:3.12.3-slim-bookworm

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local /usr/local

# Copy your project
COPY . .

EXPOSE 8000
EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]