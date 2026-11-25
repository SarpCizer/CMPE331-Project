FROM node:24-bookworm-slim AS web
WORKDIR /build/frontend
ENV CI=true
RUN npm install --global pnpm@11.25.0
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    FRONTEND_DIST=/app/frontend/dist
WORKDIR /app
COPY backend/requirements-runtime.lock /app/backend/requirements-runtime.lock
RUN pip install --no-cache-dir -r /app/backend/requirements-runtime.lock
COPY backend/ /app/backend/
RUN pip install --no-cache-dir --no-deps /app/backend \
    && useradd --create-home --uid 10001 fridgely
COPY --from=web /build/frontend/dist /app/frontend/dist
COPY scripts/cloud/start.sh /app/start.sh
USER fridgely
EXPOSE 10000
CMD ["sh", "/app/start.sh"]
