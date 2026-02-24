def score_response(response: str, expected_keywords: list) -> dict:
    """
    Bewertet eine LLM-Antwort basierend auf Keywords und Struktur.
    Gibt ein Dict mit Einzel-Scores und dem Gesamt-Score zurück.
    """
    score = 100
    matched_keywords = []
    
    # 1. Check: Leere Antwort
    if not response or len(response.strip()) == 0:
        return {"final_score": 0, "reason": "Empty response", "matches": []}

    # 2. Keyword Matching (Case Insensitive)
    if expected_keywords:
        match_count = 0
        for kw in expected_keywords:
            if kw.lower() in response.lower():
                match_count += 1
                matched_keywords.append(kw)
        
        # Abzug, wenn Keywords fehlen (proportional)
        match_ratio = match_count / len(expected_keywords)
        if match_ratio < 1.0:
            score -= (1.0 - match_ratio) * 50  # Bis zu 50 Punkte Abzug

    # 3. Längen-Check (Sanity Check)
    # Zu kurz (unter 20 Zeichen) deutet oft auf Verweigerung oder Fehler hin
    if len(response) < 20:
        score -= 20
    
    # Zu lang (über 5000 Zeichen) könnte ein Loop/Halluzination sein
    if len(response) > 5000:
        score -= 10

    return {
        "final_score": max(0, int(score)),
        "matched_keywords": matched_keywords,
        "length": len(response)
    }