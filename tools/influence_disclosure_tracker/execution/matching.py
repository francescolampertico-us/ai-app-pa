import re
from rapidfuzz import fuzz

# Common legal suffixes to remove during normalization
LEGAL_SUFFIXES = [
    r'\binc\b\.?', r'\bincorporated\b',
    r'\bllc\b\.?', r'\bl\.l\.c\.\b', r'\blimited liability company\b',
    r'\bltd\b\.?', r'\blimited\b',
    r'\bcorp\b\.?', r'\bcorporation\b',
    r'\bco\b\.?', r'\bcompany\b',
    r'\bplc\b\.?',
    r'\bgmbh\b\.?',
    r'\bs\.a\.\b',
    r'\bllp\b\.?'
]

def normalize_name(name: str) -> str:
    """Lowercases, removes punctuation, trims whitespace, drops legal suffixes."""
    if not isinstance(name, str):
        return ""
    
    # Lowercase
    n = name.lower()
    
    # Remove punctuation except spaces
    n = re.sub(r'[^\w\s]', ' ', n)
    
    # Remove legal suffixes
    for suffix in LEGAL_SUFFIXES:
        n = re.sub(suffix, '', n)
    
    # Condense whitespace
    n = re.sub(r'\s+', ' ', n).strip()
    return n

def match_entity(query_name: str, target_name: str, fuzzy_threshold: float = 85.0) -> dict:
    """
    Compares query against target and returns match type and confidence.
    Match types: 'exact', 'contains', 'fuzzy', 'none'
    Returns: {"match": bool, "match_type": str, "confidence": float}
    """
    if not query_name or not target_name:
        return {"match": False, "match_type": "none", "confidence": 0.0}
        
    q_norm = normalize_name(query_name)
    t_norm = normalize_name(target_name)
    
    if not q_norm or not t_norm:
        return {"match": False, "match_type": "none", "confidence": 0.0}

    # 1. Exact Normal Match
    if q_norm == t_norm:
        return {"match": True, "match_type": "exact", "confidence": 100.0}
        
    # 2. Contains Match (Query is fully inside Target, e.g., "apple" in "apple holding")
    # or vice versa (Target fully inside Query, e.g., "boeing" in "boeing defense")
    if q_norm in t_norm or t_norm in q_norm:
        # Penalize slightly for not being exact length
        len_diff = abs(len(q_norm) - len(t_norm))
        confidence = max(90.0, 99.0 - (len_diff * 0.5))
        return {"match": True, "match_type": "contains", "confidence": round(confidence, 1)}
        
    # 3. Fuzzy Ratio
    # token_set_ratio ignores word order and duplicated words
    score = fuzz.token_set_ratio(q_norm, t_norm)
    
    if score >= fuzzy_threshold:
        return {"match": True, "match_type": "fuzzy", "confidence": round(score, 1)}
        
    return {"match": False, "match_type": "none", "confidence": round(score, 1)}
