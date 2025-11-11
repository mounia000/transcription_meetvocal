# backend/IA/cleaning.py
import re

FILLERS_REMOVE = ["euh", "hum", "ben", "genre", "bah", "hein", "quoi", 
    "voilà", "en fait", "du coup", "donc euh"]
CONNECTORS = ["alors", "du coup", "en fait", "voilà", "donc", "ensuite", 
    "par conséquent", "d'ailleurs", "cependant", "néanmoins"]
INTERROGATIVE_STARTS = (
    "qui", "que", "quoi", "où", "quand", "comment", "pourquoi",
    "est-ce que", "n'est-ce pas", "quel", "quelle", "quels", "quelles"
)

def clean_text(text: str) -> str:
    """
    Nettoie le texte transcrit en :
    - Supprimant les mots de remplissage (euh, hum, etc.)
    - Corrigeant la ponctuation
    - Ajoutant des majuscules appropriées
    - Gérant les connecteurs
    - Supprimant les répétitions
    """
    
    #Normalisation de base
    text = text.replace("\r", " ").strip()
    text = re.sub(r"\s+", " ", text)
    
    # Suppression des mots de remplissage
    fillers_pattern = r"\b(" + "|".join([re.escape(f) for f in FILLERS_REMOVE]) + r")\b\s*"
    text = re.sub(fillers_pattern, "", text, flags=re.IGNORECASE)


    # gestion des connecteurs
    conn_pattern = r"\b(" + "|".join([re.escape(c) for c in CONNECTORS]) + r")\b\s+"
    text = re.sub(conn_pattern, lambda m: m.group(1) + ", ", text, flags=re.IGNORECASE)

    
    # Suppression des répétitions
    text = re.sub(r'\b(\w+(?: \w+){0,3})\s+\1\b', r'\1', text, flags=re.IGNORECASE)

    # Correction de Ponctuation
    # Supprime espaces avant ponctuation
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    # Ajoute espace après ponctuation si manquant
    text = re.sub(r'([,.!?;:])([^\s])', r'\1 \2', text)
    # Supprime points multiples
    text = re.sub(r'\.+', '.', text)

    # Gestion des phrases
    sentences = re.split(r'(?<=[.!?])\s+', text)
    cleaned_sentences = []
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        
        # Ajouter ponctuation finale si manquante
        if s[-1] not in ".!?":
            low = s.lower()
            # Vérifier si c'est une question
            if any(low.startswith(k) for k in INTERROGATIVE_STARTS) or "est-ce que" in low:
                s = s + " ?"
            else:
                s = s + "."
        
        # Majuscule en début de phrase
        if len(s) > 0:
            s = s[0].upper() + s[1:] if len(s) > 1 else s.upper()
        
        cleaned_sentences.append(s)
    return " ".join(cleaned_sentences)

# 6️⃣ Reconstruire le texte
    result = " ".join(cleaned_sentences)
    
    # 7️⃣ Nettoyages finaux
    # Supprimer espaces multiples
    result = re.sub(r'\s+', ' ', result)
    # Corriger "? ." ou ". ?" en un seul
    result = re.sub(r'[.!?]\s*[.!?]', '.', result)
    
    return result.strip()

def advanced_clean(text: str) -> str:
    """
    Nettoyage avancé avec des règles supplémentaires pour améliorer la lisibilité.
    """
    text = clean_text(text)
    
    # Remplacer certaines formulations orales par des versions écrites
    replacements = {
        r"\bparce que\b": "car",
        r"\bd'accord\b": "OK",
        r"\bça marche\b": "d'accord",
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text