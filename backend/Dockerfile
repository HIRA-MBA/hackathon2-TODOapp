# Stage 1: Builder
FROM python:3.13-slim AS builder
WORKDIR /app

# Install uv package manager
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock README.md ./

# Create virtual environment and install dependencies only (not the project itself)
RUN uv venv .venv && \
    uv sync --frozen --no-dev --no-install-project

# Stage 2: Runner
FROM python:3.13-slim AS runner
WORKDIR /app

# Create non-root user for security
RUN groupadd --system --gid 1001 appgroup && \
    useradd --system --uid 1001 --gid appgroup appuser

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv ./.venv

# Copy application code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Set correct ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
