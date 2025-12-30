FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

# Install SWI-Prolog and minimal system deps
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        swi-prolog \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies for the Prolog API
COPY requirements_prolog_api.txt /app/requirements_prolog_api.txt
RUN pip install --no-cache-dir -r /app/requirements_prolog_api.txt

# Copy application source
COPY . /app

# Port used by prolog_api.py (falls back to PORT env var)
EXPOSE 5001

# Run the API
CMD ["python", "prolog_api.py"]
