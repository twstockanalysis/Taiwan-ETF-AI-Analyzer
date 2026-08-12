FROM python:3.13.7-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock
COPY backend ./backend
COPY frontend ./frontend

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data /ops \
    && chown -R appuser:appuser /app /data /ops
USER appuser
