# backend/IA/cleaning.py
import re

FILLERS_REMOVE = ["euh", "hum", "ben", "genre"]
CONNECTORS = ["alors", "du coup", "en fait", "voilà", "donc", "ensuite", "par conséquent", "d'ailleurs"]
INTERROGATIVE_STARTS = (
    "qui", "que", "quoi", "où", "quand", "comment", "pourquoi",
    "est-ce que", "n'est-ce pas"
)

def clean_text(text: str) -> str:
    text = text.replace("\r", " ").strip()
    text = re.sub(r"\s+", " ", text)

    # Connecteurs
    conn_pattern = r"\b(" + "|".join([re.escape(c) for c in CONNECTORS]) + r")\b\s+"
    text = re.sub(conn_pattern, lambda m: m.group(1) + ", ", text, flags=re.IGNORECASE)

    # Fillers
    fillers_pattern = r"\b(" + "|".join([re.escape(f) for f in FILLERS_REMOVE]) + r")\b\s*"
    text = re.sub(fillers_pattern, "", text, flags=re.IGNORECASE)

    # Répétitions
    text = re.sub(r'\b(\w+(?: \w+){0,3})\s+\1\b', r'\1', text, flags=re.IGNORECASE)

    # Ponctuation
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.sub(r'([,.!?;:])([^\s])', r'\1 \2', text)
    text = re.sub(r'\.+', '.', text)

    sentences = re.split(r'(?<=[.!?])\s+', text)
    cleaned = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if s[-1] not in ".!?":
            low = s.lower()
            if any(low.startswith(k) for k in INTERROGATIVE_STARTS) or "est-ce que" in low:
                s = s + "?"
            else:
                s = s + "."
        s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
        cleaned.append(s)

    return " ".join(cleaned)
