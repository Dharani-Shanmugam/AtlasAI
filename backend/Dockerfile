FROM python:3.12-slim

WORKDIR /app

# Install only production dependencies.
COPY pyproject.toml ./
COPY app ./app
RUN pip install --no-cache-dir .

# Create data directory for SQLite + ChromaDB.
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
