# Stage 1: Build React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Copy built frontend into static/
COPY --from=frontend-builder /app/frontend/dist ./static
EXPOSE 7860
CMD ["uvicorn", "openenv_email_triage.api:app", "--host", "0.0.0.0", "--port", "7860"]
