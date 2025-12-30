FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

# Install SWI-Prolog and minimal system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        swi-prolog \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies for the merged Flask app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source
COPY . /app

# Port used by Flask app (reads PORT env var)
EXPOSE 5000

# Use Gunicorn (production WSGI). Use shell form so $PORT expands at runtime.
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:${PORT:-5000} app:app"]
