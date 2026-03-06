# Dockerfile für MCP-HTTP-SSE Server

FROM python:3.11-slim

WORKDIR /app

# System-Deps + Python-Deps in einem Layer (kein apt-Cache im Image)
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Requirements zuerst kopieren → besseres Layer-Caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Quellcode kopieren
COPY . .

# Non-root User anlegen und Workdir übergeben
# (Server schreibt objects.db und clont das Repo zur Laufzeit in /app)
RUN adduser --disabled-password --gecos "" appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 3124

CMD ["python", "server.py"]
