FROM python:3.11-slim

# Install FFmpeg et dépendances système
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Créer dossier app
WORKDIR /app

# Copier requirements et installer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY . .

# Créer dossier output
RUN mkdir -p /tmp/shorts_output

# Exposer port
EXPOSE 8000

# Lancer l'API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
