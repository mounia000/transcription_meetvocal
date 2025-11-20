# backend/app/DataBase/DB.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
import os

# Charger les variables d’environnement (.env)
load_dotenv()

# Récupérer la variable de connexion depuis ton .env
DATABASE_URL = os.getenv("DATABASE_URL")

# Créer le moteur de connexion
engine = create_engine(DATABASE_URL)

# Créer une session pour interagir avec la base
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base SQLAlchemy (si un jour tu veux créer des modèles)
Base = declarative_base()
