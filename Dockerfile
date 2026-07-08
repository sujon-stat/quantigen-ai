# Stage 1: Build Frontend Single Page Application
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python & R Runtime
FROM python:3.12-slim
WORKDIR /app

# Install system dependencies required for Kaleido PNG export and R statistical integration
RUN apt-get update && apt-get install -y --no-install-recommends \
    libfontconfig1 \
    libxrender1 \
    libxext6 \
    libnss3 \
    r-base-core \
    && rm -rf /var/lib/apt/lists/*

# Install uv for ultra-fast package installation
RUN pip install --no-cache-dir uv

# Copy project requirements and install dependencies system-wide
COPY pyproject.toml ./
RUN uv pip install --system .

# Copy backend codebase and R templates
COPY backend ./backend
COPY r_templates ./r_templates
COPY README.md ./

# Copy compiled production frontend from Stage 1
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Expose universal HTTP port
EXPOSE 8000

# Launch unified Uvicorn server hosting both REST API (/api/v1) and React SPA (/)
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
