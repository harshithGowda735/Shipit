
# 1. Start with Python 3.12
FROM python:3.12-slim

# 2. Set the working directory
WORKDIR /app

# 3. Copy dependency list
COPY requirements.txt .

# 4. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the application and migration configuration
COPY app/ ./app/
COPY migrations/ ./migrations/
COPY alembic.ini .

# 6. Expose application port
EXPOSE 8000

# 7. Start FastAPI using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
