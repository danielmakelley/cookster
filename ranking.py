from rank_bm25 import BM25Okapi
from typing import List
import re
import os
import json

# small stopword list; can be expanded
STOPWORDS = set(['the', 'a', 'an', 'and', 'or', 'of', 'in', 'on', 'with', 'to', 'for', 'by', 'from'])

# default synonyms map (can be extended from thesaurus.json)
SYNONYMS = {
    'garbanzo': 'chickpea',
    'chick peas': 'chickpea',
}

# Try to load an external thesaurus.json from the repository root to allow
# domain-specific and locale mappings (e.g., aubergine -> eggplant).
try:
    _here = os.path.dirname(__file__)
    _th_path = os.path.join(_here, 'thesaurus.json')
    if os.path.exists(_th_path):
        with open(_th_path, 'r', encoding='utf8') as f:
            data = json.load(f)
            # normalize keys/values to lowercase
            for k, v in data.items():
                if isinstance(k, str) and isinstance(v, str):
                    SYNONYMS[k.lower()] = v.lower()
except Exception:
    # best-effort: missing file or parse errors shouldn't break search
    pass


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    # First, replace any multi-word synonym keys in the raw text so they
    # become a single token or their mapped value before tokenization.
    # Sort keys by length to prefer longer (phrase) matches.
    phrase_keys = [k for k in SYNONYMS.keys() if ' ' in k]
    phrase_keys.sort(key=lambda x: -len(x))
    for pk in phrase_keys:
        pv = SYNONYMS.get(pk)
        if not pv:
            continue
        # word-boundary replace of the phrase with its mapped single-token value
        text = re.sub(r"\b" + re.escape(pk) + r"\b", pv, text)

    tokens = re.findall(r"\w+", text)
    # expand synonyms for single-token keys
    expanded = []
    for t in tokens:
        if t in SYNONYMS:
            expanded.append(SYNONYMS[t])
        else:
            expanded.append(t)
    # remove stopwords
    return [t for t in expanded if t not in STOPWORDS]


def rank_recipes(candidates: list, query: str, top_n: int = 10):
    """Candidates: list of dicts with keys id,title,ingredients,steps,source
    Returns top_n candidates sorted by BM25 score with added 'score' key."""
    if not candidates:
        return []

    # Build tokenized corpora: full-text and titles-only. We'll combine
    # BM25 scores with a higher weight on title matches so that results
    # with query terms in the title are preferred.
    corpus_full = [ _tokenize((c.get('title') or '') + ' ' + (c.get('ingredients') or '') + ' ' + (c.get('steps') or '')) for c in candidates]
    corpus_title = [ _tokenize((c.get('title') or '')) for c in candidates]

    qtokens = _tokenize(query)
    if not any(qtokens):
        for c in candidates:
            c['score'] = 0.0
        return candidates[:top_n]

    bm25_full = BM25Okapi(corpus_full)
    bm25_title = BM25Okapi(corpus_title)

    scores_full = bm25_full.get_scores(qtokens)
    try:
        scores_title = bm25_title.get_scores(qtokens)
    except Exception:
        # titles may be empty; fallback to zeros
        scores_title = [0.0] * len(candidates)

    # Combine scores: give title matches more influence
    TITLE_WEIGHT = 2.0
    combined = [float(f + TITLE_WEIGHT * t) for f, t in zip(scores_full, scores_title)]
    for c, s in zip(candidates, combined):
        c['score'] = s
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return candidates[:top_n]
