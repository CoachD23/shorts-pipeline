"""Auto-hook detection — find the most engaging sentence for thumbnail text."""
import re


# Words/patterns that indicate hook-worthy content
HOOK_SIGNALS = [
    r"\b(?:never|always|every|best|worst|biggest|number one|top)\b",
    r"\b(?:mistake|secret|trick|hack|tip|key|rule)\b",
    r"\b(?:stop|don't|won't|can't|shouldn't)\b",
    r"\b(?:destroys?|breaks?|beats?|kills?|dominates?|unlocks?)\b",
    r"\b(?:why|how|what if)\b",
    r"\b(?:most coaches|nobody|everyone)\b",
    r"\?\s*$",  # Questions
]

# Basketball-specific hook signals
BASKETBALL_SIGNALS = [
    r"\b(?:offense|defense|zone|man|press|screen|pick|roll|backdoor|cut)\b",
    r"\b(?:princeton|motion|flex|triangle|horns|floppy)\b",
    r"\b(?:drill|play|set|action|read|counter)\b",
]


def score_sentence(sentence: str) -> float:
    """Score a sentence for hook potential (0.0 - 1.0).

    Higher scores = more likely to grab attention as thumbnail text.
    """
    score = 0.0
    text = sentence.lower().strip()

    if not text or len(text) < 10:
        return 0.0

    # General hook signals
    for pattern in HOOK_SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.15

    # Basketball-specific signals
    for pattern in BASKETBALL_SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            score += 0.1

    # Shorter sentences make better hooks (3-7 words ideal)
    word_count = len(text.split())
    if 3 <= word_count <= 7:
        score += 0.2
    elif word_count <= 10:
        score += 0.1

    # Sentences at the start of the transcript are often hooks
    # (handled by caller with position bonus)

    return min(score, 1.0)


def detect_hook(transcript: dict, max_words: int = 5) -> dict:
    """Find the best hook sentence from a transcript.

    Args:
        transcript: Whisper transcript with text and segments.
        max_words: Maximum words for the suggested thumbnail text.

    Returns:
        Dict with:
            - 'sentence': The full hook sentence
            - 'hook_text': Shortened version for thumbnail (max_words)
            - 'accent_word': Suggested accent word (most impactful)
            - 'score': Hook score (0.0 - 1.0)
    """
    full_text = transcript.get("text", "")
    sentences = re.split(r"(?<=[.!?])\s+", full_text)

    if not sentences or not any(s.strip() for s in sentences):
        return {"sentence": "", "hook_text": "", "accent_word": "", "score": 0.0}

    # Score each sentence with position bonus
    scored = []
    for i, sentence in enumerate(sentences):
        base_score = score_sentence(sentence)
        # Position bonus: first 3 sentences get a boost
        position_bonus = max(0, 0.15 - (i * 0.05))
        scored.append((sentence.strip(), base_score + position_bonus))

    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    best_sentence, best_score = scored[0]

    # Shorten to max_words for thumbnail
    words = best_sentence.rstrip(".!?").split()
    hook_words = words[:max_words]
    hook_text = " ".join(hook_words).upper()

    # Pick accent word: last noun/verb or the most impactful word
    accent_candidates = [w for w in hook_words if len(w) >= 4]
    accent_word = accent_candidates[-1].upper() if accent_candidates else hook_words[-1].upper()

    return {
        "sentence": best_sentence,
        "hook_text": hook_text,
        "accent_word": accent_word,
        "score": best_score,
    }
