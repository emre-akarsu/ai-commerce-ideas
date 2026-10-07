# API image (built from the repo root: docker build -f deploy/docker/Dockerfile .). Runs as a
# non-root user; holds no mail credentials (nothing is sent by this image).
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY pyproject.toml ./
COPY packages ./packages
COPY apps ./apps
COPY employees ./employees
COPY profiles ./profiles
COPY scripts ./scripts
COPY src ./src
RUN pip install -e . && useradd --system --uid 10001 --no-create-home rfq
ENV PYTHONPATH=/app/packages:/app
USER rfq
EXPOSE 8000
CMD ["python", "scripts/demo_api.py", "--host", "0.0.0.0", "--port", "8000"]
