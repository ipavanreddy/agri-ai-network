# Build context = repository root (the API reads ../../ai/prompts and ../../data at runtime):
#   docker build -f services/api/Dockerfile -t agri-ai-network-api .
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
# Mirror the repo layout so app/config.py::REPO_ROOT (parents[3] of the module) resolves to /srv.
WORKDIR /srv/services/api
COPY services/api/pyproject.toml services/api/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY services/api/app ./app
COPY ai/prompts /srv/ai/prompts
COPY ai/schemas /srv/ai/schemas
COPY data/adapters /srv/data/adapters
COPY data/sample /srv/data/sample
COPY data/schemas /srv/data/schemas
RUN useradd --uid 10001 --no-create-home app && mkdir -p .data && chown -R app .data
USER app
ENV PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
