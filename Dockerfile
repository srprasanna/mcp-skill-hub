# Stage 1: Builder
FROM python:3.13-slim as builder

# Build argument for version
ARG VERSION=0.1.0

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

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

# Build argument for version (must be redeclared in each stage)
ARG VERSION=0.1.0

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

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import mcp_skills; print('OK')" || exit 1

# Expose volume for skills
VOLUME ["/skills"]

# Labels
LABEL org.opencontainers.image.title="MCP Skills Server" \
      org.opencontainers.image.description="Dynamic skill loading MCP server with hot-reload support" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.vendor="Beehyv" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.source="https://github.com/srprasanna/mcp-skill-hub" \
      io.modelcontextprotocol.server.name="io.github.srprasanna/mcp-skill-hub"

# Entry point
ENTRYPOINT ["python", "-m", "mcp_skills"]
