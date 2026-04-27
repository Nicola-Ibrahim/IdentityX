# ============================================================
#  Stage 1 — deps: install uv and system build dependencies
# ============================================================
FROM python:3.12-slim AS deps

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential libpq-dev \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:${PATH}"
WORKDIR /app
COPY uv.lock pyproject.toml ./

# ============================================================
#  Stage 2 — dev: full deps + hot-reload
#  Usage:  target: dev
# ============================================================
FROM deps AS dev
# Install ALL dependencies (including dev, test, lint groups)
RUN uv sync --frozen --no-install-project
COPY . .
# Put the virtualenv on the PATH so 'fastapi' is available natively
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uv", "run", "fastapi", "dev", "src/api/main.py", "--host", "0.0.0.0", "--port", "8000"]

# ============================================================
#  Stage 3 — builder: production deps only
# ============================================================
FROM deps AS builder
RUN uv sync --frozen --no-install-project --no-dev

# ============================================================
#  Stage 4 — runner: minimal production image
#  Usage:  target: runner  (default)
# ============================================================
FROM python:3.12-slim AS runner

RUN apt-get update && apt-get install -y --no-install-recommends libpq5 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY . /app

# Put the virtualenv on the PATH so 'python' refers to the one with our deps
ENV PATH="/app/.venv/bin:$PATH"

# Copy entrypoint script and make it executable
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Security: Non-root user
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["fastapi", "run", "src/api/main.py", "--port", "8000"]
