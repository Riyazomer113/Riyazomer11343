FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source, frontend, and database
COPY app ./app
COPY frontend ./frontend
COPY signalhunt.db ./signalhunt.db

# Configuration defaults
ENV PORT=8000 \
    ADMIN_PASSWORD=ISLIEEEECELL \
    DATABASE_PATH=/app/signalhunt.db \
    MAX_TEAMS=12 \
    MAX_PARTICIPANTS_PER_TEAM=5 \
    MAX_TOTAL_PARTICIPANTS=60 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
