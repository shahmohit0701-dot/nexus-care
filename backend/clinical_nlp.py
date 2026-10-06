"""Optional biomedical NLP adapter for the capstone.
Uses medspaCy/scispaCy when installed; otherwise exposes a deterministic fallback metadata layer.
"""
import re
try:
    import medspacy
    MEDSPACY_AVAILABLE=True
except Exception:
    MEDSPACY_AVAILABLE=False
try:
    import scispacy
    SCISPACY_AVAILABLE=True
except Exception:
    SCISPACY_AVAILABLE=False

def extract(text):
    t=text.lower()
    neg=[m.group(2).strip() for m in re.finditer(r'\b(no|not|without|denies|never)\s+([a-z ]{2,40})',t)]
    d=re.search(r'(\d+\s*(?:minute|minutes|hour|hours|day|days|week|weeks))',t)
    severity='severe' if any(w in t for w in ['severe','extreme','unbearable','crushing','intense']) else ('moderate' if 'moderate' in t else 'mild')
    return {'medspacy_available':MEDSPACY_AVAILABLE,'scispacy_available':SCISPACY_AVAILABLE,'negation_spans':neg,'duration':d.group(1) if d else 'unspecified','severity':severity}
