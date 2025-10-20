import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

def speach_to_text(audio_path, language="fr"):
    client = Groq(api_key=os.environ["GROQ_API_KEY"])

    with open(audio_path, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=file,
            model="whisper-large-v3-turbo",
            prompt="Extrait le texte de l'audio de la manière la plus factuelle possible",
            response_format="verbose_json",
            timestamp_granularities=["word", "segment"],
            language=language,
            temperature=0.0
        )
        return transcription.text


if __name__ == "__main__":
    # ✅ Chemin relatif basé sur l'emplacement du script
    base_dir = os.path.dirname(__file__)
    audio_path = os.path.join(base_dir, "audio", "meet.m4a")

    text = speach_to_text(audio_path, language="fr")
    print(text)
