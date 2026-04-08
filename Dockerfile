# Stage 1: Build React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Copy built frontend from static/ (vite builds to ../static)
COPY --from=frontend-builder /app/static ./static
EXPOSE 7860
CMD ["uvicorn", "openenv_email_triage.api:app", "--host", "0.0.0.0", "--port", "7860"]
