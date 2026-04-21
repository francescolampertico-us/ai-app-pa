FROM python:3.11-slim

WORKDIR /app

COPY fastapi-backend/requirements.txt fastapi-backend/requirements.txt
RUN pip install --no-cache-dir -r fastapi-backend/requirements.txt

COPY . .

WORKDIR /app/fastapi-backend
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]
