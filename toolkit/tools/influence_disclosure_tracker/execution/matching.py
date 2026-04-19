import re
from rapidfuzz import fuzz

# Words that are generic in diplomatic/government entity names and should not
# be used as distinguishing identifiers when matching.
DIPLOMATIC_GENERIC = {
    "embassy", "embassies", "state", "states", "government", "governments",
    "royal", "nation", "national", "republic", "kingdom", "ministry", "mission",
    "consulate", "permanent", "through", "via", "including", "behalf",
    "of", "the", "on", "by", "for", "and", "in", "an", "a",
    "islamic", "plurinational", "democratic", "peoples", "federal", "united",
}

def get_content_tokens(norm_name: str) -> set:
    """Return the non-generic tokens from a normalized name."""
    return set(norm_name.split()) - DIPLOMATIC_GENERIC

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

    # 1. Exact Match
    if q_norm == t_norm:
        return {"match": True, "match_type": "exact", "confidence": 100.0}

    # 2. Content token match — handles diplomatic name variations
    # "Embassy of the State of Qatar", "State of Qatar", "Qatar" all → {"qatar"}
    # "Embassy of Kuwait" → {"kuwait"} — correctly does NOT match Qatar
    q_content = get_content_tokens(q_norm)
    t_content = get_content_tokens(t_norm)
    if q_content and t_content and (q_content == t_content or
                                     q_content.issubset(t_content) or
                                     t_content.issubset(q_content)):
        len_diff = abs(len(q_content) - len(t_content))
        confidence = max(85.0, 95.0 - (len_diff * 5.0))
        return {"match": True, "match_type": "contains", "confidence": round(confidence, 1)}

    # 3. Fuzzy Ratio
    # token_sort_ratio requires all tokens to be present (stricter than token_set_ratio)
    score = fuzz.token_sort_ratio(q_norm, t_norm)

    if score >= fuzzy_threshold:
        return {"match": True, "match_type": "fuzzy", "confidence": round(score, 1)}
        
    return {"match": False, "match_type": "none", "confidence": round(score, 1)}
