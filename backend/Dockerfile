# Stage 1: install dependencies
FROM python:3.12-slim AS builder

WORKDIR /install

COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


# Stage 2: runtime image
FROM python:3.12-slim

RUN groupadd --gid 1001 appuser && \
    useradd --uid 1001 --gid 1001 --no-create-home appuser

WORKDIR /app

COPY --from=builder /install/lib /usr/local/lib
COPY --from=builder /install/bin /usr/local/bin

COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini .
COPY gunicorn.conf.py .
COPY start.sh .

RUN chmod +x start.sh

USER appuser

EXPOSE 8000

CMD ["./start.sh"]
