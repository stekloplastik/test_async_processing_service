FROM python:3.10-slim as builder

RUN pip install poetry==2.0.1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Install dependencies (without installing the root app)
RUN poetry install --no-root --only main && rm -rf $POETRY_CACHE_DIR

FROM python:3.10-slim as runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy python virtual environment and source code
COPY --from=builder /app/.venv /app/.venv
COPY app /app/app
COPY alembic.ini /app/alembic.ini

EXPOSE 8000
