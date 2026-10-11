# Single container: builds the React frontend, then serves it and the
# FastAPI backend from one origin (keeps the owner cookie first-party).

# --- Stage 1: build the frontend ---
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
# Empty base URL = relative "/api/..." requests to the same origin.
ENV VITE_API_BASE_URL=""
RUN npm run build

# --- Stage 2: backend + built frontend ---
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FRONTEND_DIST_DIR=/app/static \
    UPLOAD_DIR=/tmp/uploads

# ffmpeg/ffprobe: duration probing + silence-based chunking of long audio.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY --from=frontend /frontend/dist ./static

# Render injects PORT; default for running the image locally.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
