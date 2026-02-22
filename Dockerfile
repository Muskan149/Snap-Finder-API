# SNAP Finder API – run with: docker build -t snap-finder-api . && docker run -p 8000:8000 snap-finder-api
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code and data (CSV stays in project root; copy all to avoid quoting filename with spaces)
COPY . .

# Use PORT from env (e.g. 8000); many platforms set PORT
ENV PORT=8000
EXPOSE $PORT

CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
