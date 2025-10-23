# Stage 1: Builder
FROM python:3.13-slim as builder

# Install Poetry
RUN pip install poetry==1.7.1

# Configure Poetry to not create virtual env (we're in container)
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --without dev --no-root

# Stage 2: Runtime
FROM python:3.13-slim as runtime

# Create non-root user
RUN useradd -m -u 1000 appuser

# Copy virtual environment from builder
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

# Copy application code
WORKDIR /app
COPY src ./src

# Create skills directory
RUN mkdir -p /skills && chown appuser:appuser /skills

# Switch to non-root user
USER appuser

# Set default environment variables
ENV MCP_SKILLS_DIR=/skills \
    MCP_SKILLS_HOT_RELOAD=true \
    MCP_SKILLS_LOG_LEVEL=INFO

# Health check (optional - for future use)
# HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
#   CMD python -c "from pathlib import Path; exit(0 if Path('/skills').exists() else 1)"

# Entry point
ENTRYPOINT ["python", "-m", "mcp_skills"]
