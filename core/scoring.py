import re

def score_response(response: str, expected_keywords: list) -> dict:
    """
    Evaluiert die Antwort des LLMs basierend auf Schlagworten.
    Gibt IMMER ein Dictionary mit dem Key 'score' zurück.
    """
    # Fallback, falls die Antwort leer oder None ist
    if not response or not isinstance(response, str):
        return {
            "score": 0,
            "matches": [],
            "missing": expected_keywords,
            "status": "No response provided"
        }

    # Falls keine Keywords definiert sind, betrachten wir die Antwort als 100% 
    # (oder man könnte 0 setzen, je nach Test-Philosophie)
    if not expected_keywords:
        return {
            "score": 100,
            "matches": [],
            "missing": [],
            "status": "No keywords to evaluate"
        }

    matches = []
    missing = []
    
    # Normalisierung für fairen Vergleich (Lowercase und Wortgrenzen beachten)
    clean_response = response.lower()
    
    for kw in expected_keywords:
        # Wir suchen mit RegEx nach dem Wort, um Teil-Treffer (wie 'Baum' in 'Baumhaus') zu finden
        if re.search(rf"\b{re.escape(kw.lower())}\b", clean_response):
            matches.append(kw)
        else:
            missing.append(kw)

    # Score-Berechnung (Prozentualer Anteil der gefundenen Wörter)
    match_count = len(matches)
    total_count = len(expected_keywords)
    
    # Sicherstellen, dass das Ergebnis ein Integer zwischen 0 und 100 ist
    final_score = int((match_count / total_count) * 100) if total_count > 0 else 0

    return {
        "score": final_score,
        "matches": matches,
        "missing": missing,
        "status": f"Found {match_count} of {total_count} keywords"
    }