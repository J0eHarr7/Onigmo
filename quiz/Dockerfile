FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Data directory for SQLite
RUN mkdir -p /data

EXPOSE 5000

ENV FLASK_ENV=production
ENV DB_PATH=/data/quiz.db
ENV ADMIN_PASS=3BLRD9P7JhcJ
ENV SECRET_KEY=one-ring-to-rule-them-all-2026

CMD ["python", "app.py"]
