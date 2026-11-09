FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

COPY app ./app
COPY migrations ./migrations

# Built-in SQLite database + generated JWT secret live here when DATABASE_URL / JWT_SECRET_KEY aren't set.
# Mount a volume on /app/data to keep that data when the container is replaced.
RUN mkdir -p /app/data && chown appuser:appgroup /app/data
VOLUME /app/data

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
