# Multi-stage build (PLAN.md §11): Next.js static export -> FastAPI + uv,
# single image, single port. Build from the project root:
#   docker build -t finally .

# ---- Stage 1: frontend static export ----
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package.json ./
# No committed package-lock.json yet, so `npm install` rather than `npm ci`.
RUN npm install
COPY frontend/ .
RUN npm run build

# ---- Stage 2: backend dependencies + assembled app ----
FROM python:3.12-slim AS backend-builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_PYTHON_DOWNLOADS=0 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# Keep the "backend" path segment in the image (WORKDIR /app/backend, not
# /app): app/db/connection.py resolves its default DB path as three parents
# above itself, matching the local dev layout finally/backend/app/db/ ->
# finally/db/. Flattening this to /app/app/db/ would break that resolution
# to a default of /db instead of /app/db (PLAN.md §11).
WORKDIR /app/backend

# Dependencies first, in their own layer — only invalidated by lockfile changes.
# No --no-dev needed: the pytest/ruff/httpx group is a PEP 621 "dev" extra
# ([project.optional-dependencies]), not a PEP 735 dependency-group, so plain
# `uv sync` already excludes it unless --extra/--all-extras is passed.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY backend/ /app/backend/
# Static export lands inside the app package before the project is synced,
# so app/main.py's STATIC_DIR (app/static, resolved via __file__) finds it
# regardless of editable-install mechanics.
COPY --from=frontend-builder /frontend/out /app/backend/app/static

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# ---- Stage 3: slim runtime image ----
FROM python:3.12-slim
RUN groupadd --system --gid 999 finally \
 && useradd --system --gid 999 --uid 999 --create-home finally

COPY --from=backend-builder --chown=finally:finally /app/backend /app/backend
ENV PATH="/app/backend/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app/backend
# Bind-mounted at runtime (docker run -v $(pwd)/db:/app/db) so finally.db
# persists on the host (PLAN.md §11).
RUN mkdir -p /app/db && chown finally:finally /app/db

USER finally
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
