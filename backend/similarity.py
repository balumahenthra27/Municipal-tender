import re
from typing import List, Set

# Common domain-specific abbreviation and synonym mappings
ABBREVIATIONS = {
    r"\blight\s+commercial\s+vehicles?\b": "lcv",
    r"\blcvs?\b": "lcv",
    r"\bsolid\s+waste(?:\s+management)?\b": "swm",
    r"\bswm\b": "swm",
    r"\bbattery\s+operated\s+vehicles?\b": "bov",
    r"\bbovs?\b": "bov",
    r"\bbio[\s\-_]*mining\b": "biomining",
    r"\bresource\s+recovery\s+parks?\b": "rr_park",
    r"\brr\s*parks?\b": "rr_park",
    r"\bmicro\s+composting\s+centers?\b": "mcc",
    r"\bmcc\b": "mcc",
    r"\bwindrow\s+pads?\b": "windrow_pad",
    r"\bstorage\s+sheds?\b": "storage_shed",
    r"\bkitchen\s+sheds?\b": "kitchen_shed",
    r"\bdining\s+hall\b": "dining_hall",
    r"\bborewells?\b": "borewell",
    r"\bdeep\s+borewells?\b": "borewell",
    r"\bpump\s*sets?\b": "pumpset",
    r"\bsubmersible\s+motor\b": "pumpset",
    r"\bdrinking\s+water\b": "water_supply",
    r"\bwater\s+supply\b": "water_supply",
    r"\bdrainages?\b": "drainage",
    r"\bdrains?\b": "drainage",
    r"\bbituminous\s+roads?\b": "bt_road",
    r"\bbt\s+roads?\b": "bt_road",
    r"\bpaver\s+blocks?\b": "paver_blocks",
    r"\bturip\b": "turip",
    r"\bsdrf\b": "sdrf",
}

# Strictly grammatical English stopwords
STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "then", "of", "at", "by",
    "for", "with", "about", "against", "between", "into", "through", "during",
    "before", "after", "above", "below", "to", "from", "up", "down", "in",
    "out", "on", "off", "over", "under", "again", "further", "then", "once",
    "here", "there", "when", "where", "why", "how", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "can",
    "will", "just", "should", "now", "is", "are", "was", "were",
    "be", "been", "being", "have", "has", "had", "having", "do", "does",
    "did", "doing", "nos", "no", "roc", "date", "per", "etc"
}

def normalize_abbreviations(text: str) -> str:
    """Normalize common municipal and Solid Waste Management abbreviations."""
    lowered = text.lower()
    for pattern, replacement in ABBREVIATIONS.items():
        lowered = re.sub(pattern, replacement, lowered)
    return lowered

def normalize_text(text: str) -> str:
    """Lowercase, normalize abbreviations, clean special characters."""
    if not text:
        return ""
    text = normalize_abbreviations(text)
    # Replace non-alphanumeric (except underscores) with space
    text = re.sub(r"[^a-zA-Z0-9_]+", " ", text)
    return text.strip()

def tokenize(text: str) -> List[str]:
    """Tokenize normalized text."""
    if not text:
        return []
    normalized = normalize_text(text)
    return [t for t in normalized.split() if len(t) > 1]

def remove_stopwords(tokens: List[str]) -> List[str]:
    """Filter out common stopwords from token list."""
    return [t for t in tokens if t not in STOPWORDS]

def get_clean_keywords(text: str) -> Set[str]:
    """Extract processed unique keyword set."""
    tokens = tokenize(text)
    filtered = remove_stopwords(tokens)
    return set(filtered)

def keyword_similarity(text1: str, text2: str) -> float:
    """
    Calculate transparent keyword similarity between two procurement texts.
    Uses Dice-Sørensen coefficient and token overlap for balanced score.
    Returns 0.0 to 1.0 rounded to 2 decimal places.
    """
    tokens1 = get_clean_keywords(text1)
    tokens2 = get_clean_keywords(text2)

    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1.intersection(tokens2)
    if not intersection:
        return 0.0
    
    # Sørensen-Dice coefficient: 2 * |A ∩ B| / (|A| + |B|)
    dice = (2.0 * len(intersection)) / (len(tokens1) + len(tokens2))
    
    # Jaccard index: |A ∩ B| / |A ∪ B|
    union = tokens1.union(tokens2)
    jaccard = len(intersection) / len(union) if union else 0.0
    
    # Weighted combination: 70% Dice, 30% Jaccard
    score = (0.7 * dice) + (0.3 * jaccard)
    return round(score, 2)

if __name__ == "__main__":
    t1 = "Supply of Light Commercial Vehicle for solid waste collection"
    t2 = "Supply and delivery of LCV for SWM"
    score = keyword_similarity(t1, t2)
    print(f"Tokens 1: {get_clean_keywords(t1)}")
    print(f"Tokens 2: {get_clean_keywords(t2)}")
    print(f"Similarity: {score}")
