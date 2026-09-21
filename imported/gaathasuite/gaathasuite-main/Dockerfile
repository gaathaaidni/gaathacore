# Stage 1: Build React frontend
ARG BUILD_ID=unknown
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package manifests and install dependencies to leverage Docker cache.
COPY frontend/package.json frontend/package-lock.json* ./
# Using npm ci is recommended for CI/CD environments for faster, more reliable builds.
RUN npm ci

# Copy Vite config, index.html, and source directories
COPY frontend/vite.config.js ./
COPY frontend/index.html ./
COPY frontend/public ./public
COPY frontend/src ./src
RUN npm run build
# Embed build identifier (passed with --build-arg) into the built frontend for verification
RUN printf '%s\n' "${BUILD_ID:-unknown}" > /app/frontend/static/dist/build-id.txt

# Stage 2: Build Python dependencies
FROM python:3.11-slim AS python-builder

WORKDIR /app/backend

# Install build-time dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libcairo2-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir=/wheels -r requirements.txt

# Stage 3: Final image
FROM python:3.11-slim

WORKDIR /app/backend
ENV PYTHONPATH=/app/backend

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libcairo2 \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY --from=python-builder /wheels /wheels
RUN pip install --no-cache --no-index --find-links=/wheels /wheels/*

COPY backend/ ./

# Copy built frontend assets from the frontend-builder stage into backend static folder
# Vite is configured to output to static/dist
COPY --from=frontend-builder /app/frontend/static/dist/ ./static/dist/

# Copy and make entrypoint executable
COPY backend/entrypoint.sh /app/backend/entrypoint.sh
RUN chmod +x /app/backend/entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/app/backend/entrypoint.sh"]