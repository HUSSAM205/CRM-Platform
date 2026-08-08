# syntax=docker/dockerfile:1
#
# Build context is the REPO ROOT (see infra/docker-compose.yml:
# build.context: .., build.dockerfile: backend/Dockerfile), because this image also
# needs the sibling `ai/` package - app/ai/embedding_client.py imports it via a
# relative path so the notebook and the backend run the exact same embedding code.

FROM python:3.12-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# psycopg[binary] and torch ship prebuilt wheels for this base image, so no compiler
# toolchain is needed here.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .
COPY ai/ /ai

EXPOSE 8000

# Applies any pending migrations, then starts the API - keeps the running app's schema
# always in sync with what actually shipped, including in a future CI/CD pipeline.
ENTRYPOINT ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
