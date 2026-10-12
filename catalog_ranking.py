"""Rank catalog items for a customer's description using embeddings plus the lexical matcher.

Only decides which catalog item a description means. Approval, single-use sales and every
transaction guard stay in project_starter.py and apply to whatever this returns.

The embedding function is passed in, so this module makes no API calls itself and can be
tested with fake vectors. If embedding fails (e.g. an API outage), it falls back to the
lexical matcher for that call.
"""
import math
from typing import Callable, Dict, List, Sequence, Union

from matching import CatalogMatcher, strip_quantity

# texts -> one embedding vector per text
EmbedFn = Callable[[List[str]], List[Sequence[float]]]

# Tuned on a labeled set of 88 descriptions (sample-request wording, paraphrases and items we
# don't sell) with text-embedding-3-large; see evaluate_matching.py.
SHORTLIST_SIZE = 3        # only the 3 items most similar by embedding can be picked
MIN_SIMILARITY = 0.42     # below this, the description matches nothing in the catalog
EMBEDDING_WEIGHT = 1.0    # combined score = lexical score + EMBEDDING_WEIGHT * cosine similarity
MIN_COMBINED_SCORE = 0.6  # below this, the description matches nothing in the catalog


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


class HybridCatalogMatcher:
    """CatalogMatcher's rules first, then embedding shortlist, then lexical + embedding score."""

    def __init__(self, catalog: Dict[str, str], embed: EmbedFn):
        """catalog maps item name -> category; embed turns texts into vectors."""
        self.lexical = CatalogMatcher(catalog)
        self._catalog = catalog
        self._embed = embed
        self._vectors: Dict[str, Sequence[float]] = {}  # embedding cache, keyed by text
        self.fallbacks = 0  # calls answered by the lexical matcher because embedding failed

    def exact(self, item_name: str) -> Union[str, None]:
        return self.lexical.exact(item_name)

    def _vectors_for(self, texts: List[str]) -> List[Sequence[float]]:
        missing = [t for t in dict.fromkeys(texts) if t not in self._vectors]
        if missing:
            self._vectors.update(zip(missing, self._embed(missing)))
        return [self._vectors[t] for t in texts]

    def _catalog_text(self, name: str) -> str:
        return f"{name} ({self._catalog[name]})"

    def ranked(self, description: str) -> List[tuple]:
        """(combined score, cosine, item) for the shortlisted items, best first."""
        query = strip_quantity(description)
        names = list(self._catalog)
        vectors = self._vectors_for([query] + [self._catalog_text(n) for n in names])
        similarity = {name: cosine(vectors[0], vector) for name, vector in zip(names, vectors[1:])}
        shortlist = sorted(names, key=similarity.get, reverse=True)[:SHORTLIST_SIZE]
        return sorted(((self.lexical.lexical_score(query, n) + EMBEDDING_WEIGHT * similarity[n], similarity[n], n)
                       for n in shortlist), reverse=True)

    def best_match(self, description: str) -> Union[str, None]:
        decided, item = self.lexical.apply_rules(description)
        if decided:
            return item
        try:
            ranked = self.ranked(description)
        except Exception as error:  # embedding API unavailable: keep working with the lexical matcher
            self.fallbacks += 1
            print(f"WARN (catalog ranking): embedding failed ({type(error).__name__}); using the lexical matcher")
            return self.lexical.best_match(description)
        best_similarity = max(similarity for _, similarity, _ in ranked)
        combined, _, name = ranked[0]
        if best_similarity < MIN_SIMILARITY or combined < MIN_COMBINED_SCORE:
            return None
        return name
