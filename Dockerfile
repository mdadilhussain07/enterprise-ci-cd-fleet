# ==============================================================================
# STAGE 1: Build Stage (Includes build tools and wheels generation)
# ==============================================================================
FROM python:3.12-slim-bookworm AS builder

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install build dependencies required for compiling C extensions (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies as pre-built wheels in a staging directory
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# STAGE 2: Hardened Production Runtime (Minimal, Non-Root)
# ==============================================================================
FROM python:3.12-slim-bookworm AS runner

# Security: Never run containers as root in production!
# Create an unprivileged system user and group (UID/GID 10001)
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /usr/sbin/nologin -M appuser

WORKDIR /app

# Install ONLY runtime shared libraries (libpq for postgresql client)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code
COPY --chown=appuser:appgroup app.py .

# Update PATH so the unprivileged user can execute binaries from ~/.local/bin
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

# Switch execution context to the unprivileged non-root user
USER appuser

# Document exposed application port
EXPOSE 8000

# Container Healthcheck for automated daemon self-healing
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/healthz || exit 1

# Start the application server using production-tuned workers
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
