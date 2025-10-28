import os
from dotenv import load_dotenv
from pyannote.audio import Pipeline

# 1️⃣ Charger les variables d'environnement depuis .env
load_dotenv()

# 2️⃣ Vérifier que le token Hugging Face est défini
token = os.environ.get("HUGGINGFACE_TOKEN")
if not token:
    raise ValueError(
        "❌ Le token Hugging Face n'est pas défini. "
        "Ajoute-le dans ton fichier .env comme HUGGINGFACE_TOKEN=ton_token"
    )
print("✅ Token Hugging Face chargé correctement.")

# 3️⃣ Désactiver les symlinks pour Windows (Hugging Face)
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

# 3.1️⃣ Vérifier si hf_xet est installé (optionnel pour Windows)
try:
    import hf_xet
    print("✅ hf_xet est installé, les symlinks seront évités.")
except ImportError:
    print("⚠️ hf_xet n'est pas installé. Tu peux l'installer avec `pip install hf_xet` pour éviter les problèmes de symlinks sur Windows.")

# 4️⃣ Définir le chemin du fichier audio
audio_path = r"C:\Users\user\transcription_meetvocal\backend\IA\audio\meetvoc.wav"
if not os.path.exists(audio_path):
    raise FileNotFoundError(f"❌ Le fichier {audio_path} est introuvable.")
print(f"✅ Fichier audio trouvé : {audio_path}")

# 5️⃣ Charger le pipeline de diarisation
print("⏳ Chargement du pipeline de diarisation (pyannote)...")
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization",
    use_auth_token=token
   
)
print("✅ Pipeline chargé avec succès !")



# 6️⃣ Appliquer la diarisation
print(f"🎧 Diarisation du fichier : {audio_path}")
diarization = pipeline(audio_path)


# 7️⃣ Afficher les résultats et tous les intervenants détectés
speakers_set = set()
print("\n🗣️ Résultats de la diarisation :\n")
for turn, _, speaker in diarization.itertracks(yield_label=True):
    speakers_set.add(speaker)
    print(f"{speaker}: {turn.start:.1f}s -> {turn.end:.1f}s")

print("\n👥 Intervenants détectés automatiquement :", speakers_set)

