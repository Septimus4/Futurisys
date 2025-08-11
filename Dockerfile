FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY migrations ./migrations
RUN pip install --no-cache-dir .

EXPOSE 8000

ENV DATABASE_URL=postgresql+psycopg://user:pass@db:5432/zero_shot

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
