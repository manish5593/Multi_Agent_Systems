"""Match a customer's wording for an item to a single catalog item.

Pure logic: no database access and no per-request state.
"""
import difflib
import re
from typing import Iterable, List, Union

# Common customer wording that does not resemble the catalog name
CATALOG_ALIASES = {
    "printer paper": "Standard copy paper",
    "copy paper": "Standard copy paper",
    "poster board": "Large poster paper (24x36 inches)",
}

# A leading order quantity, e.g. "250,000 sheets of" or "2000", but not a spec like "250 gsm" or "100 lb"
LEADING_QUANTITY_PATTERN = re.compile(
    r"^\s*\d[\d,]*(?![\d,])(?!\s*(?:gsm|lb)\b)\s*"
    r"(?:(?:sheets?|rolls?|reams?|packets?|packs?|boxes?|units?|pieces?|pads?|pcs)\b)?\s*(?:of\b)?\s*",
    re.IGNORECASE,
)


def match_words(text: str) -> List[str]:
    """Lowercase words with punctuation removed and simple plurals singularized."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words]


def normalize_description(description: str) -> str:
    return " ".join(match_words(description))


def strip_quantity(description: str) -> str:
    """Remove a leading order quantity so its digits cannot match items like "250 gsm cardstock"."""
    return LEADING_QUANTITY_PATTERN.sub("", description, count=1)


class CatalogMatcher:
    """Matches descriptions against a fixed list of catalog item names."""

    def __init__(self, catalog_names: Iterable[str]):
        self.names = list(catalog_names)
        self._by_lower_name = {name.lower(): name for name in self.names}
        # Paper sizes the catalog stocks, e.g. {"a4"}
        self._sizes = {w for name in self.names for w in name.lower().split() if re.fullmatch(r"a\d", w)}

    def exact(self, item_name: str) -> Union[str, None]:
        """Return the exact catalog name, ignoring case and surrounding whitespace."""
        return self._by_lower_name.get(str(item_name).strip().lower())

    def best_match(self, description: str) -> Union[str, None]:
        """
        Pick the single catalog item that best matches a customer's description, or None.

        Score = share of the item's name words found in the description, plus a bonus when the
        item contains the description's main noun (its last word), plus a little string similarity
        to break ties. Items must share at least one word with the description.
        """
        exact = self.exact(description)
        if exact:
            return exact
        description = strip_quantity(description)
        query_words = set(match_words(description))
        # Main noun: last word, ignoring parenthetical details like "(white)"
        head_words = match_words(re.sub(r"\([^)]*\)", " ", description))
        head = head_words[-1] if head_words else None

        sizes = {w for w in query_words if re.fullmatch(r"a\d", w)}
        if sizes - self._sizes:
            return None  # e.g. A3 or A5: we only stock A4, so do not fuzzy-match to A4 paper
        if not sizes:
            for alias, name in CATALOG_ALIASES.items():
                if alias in normalize_description(description):
                    return name

        best_score, best_name = 0.0, None
        for name in self.names:
            name_words = set(match_words(name))
            overlap = len(query_words & name_words)
            if overlap == 0:
                continue
            score = overlap / len(name_words)
            if head in name_words:
                score += 0.5
            score += 0.25 * difflib.SequenceMatcher(None, description.lower(), name.lower()).ratio()
            if score > best_score:
                best_score, best_name = score, name
        return best_name
