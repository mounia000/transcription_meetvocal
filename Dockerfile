# Dockerfile optimisé avec PyTorch pré-installé
FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements
COPY requirements.txt .

# Créer un fichier requirements sans torch/torchaudio (déjà dans l'image de base)
RUN grep -v "^torch==" requirements.txt | grep -v "^torchaudio==" > requirements_no_torch.txt

# Installer les dépendances Python restantes
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements_no_torch.txt

# Copier le code de l'application
COPY . .

# Exposer le port
EXPOSE 8000

# Commande de démarrage
CMD ["uvicorn", "backend.api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
