"""Offline tests for catalog_ranking.py using a fake embedding function.

Run with `python -m unittest test_catalog_ranking`.
"""
import unittest

from catalog_ranking import HybridCatalogMatcher

CATALOG = {
    "A4 paper": "paper",
    "Glossy paper": "paper",
    "Cardstock": "paper",
    "100 lb cover stock": "specialty",
    "Paper cups": "product",
    "Standard copy paper": "paper",
}

# Each text gets a vector from the topics it mentions: [plain paper, glossy, heavy card, cups]
TOPICS = [("a4", "copy", "printer", "plain"), ("glossy",), ("card", "cover", "heavy"), ("cup",)]


def fake_vector(text):
    text = text.lower()
    vector = [float(any(word in text for word in words)) for words in TOPICS]
    return vector if any(vector) else [0.01, 0.01, 0.01, 0.01]


class FakeEmbedder:
    def __init__(self):
        self.texts = []

    def __call__(self, texts):
        self.texts.extend(texts)
        return [fake_vector(t) for t in texts]


class HybridCatalogMatcherTest(unittest.TestCase):
    def setUp(self):
        self.embed = FakeEmbedder()
        self.matcher = HybridCatalogMatcher(CATALOG, self.embed)

    def test_exact_name_needs_no_embedding(self):
        self.assertEqual(self.matcher.best_match("glossy PAPER"), "Glossy paper")
        self.assertEqual(self.embed.texts, [])

    def test_rules_override_embeddings(self):
        self.assertIsNone(self.matcher.best_match("A3 paper"))  # unstocked size, though "paper" is similar
        self.assertEqual(self.matcher.best_match("printer paper"), "Standard copy paper")  # alias
        self.assertEqual(self.embed.texts, [])

    def test_embeddings_pick_the_item(self):
        self.assertEqual(self.matcher.best_match("heavy card for covers"), "100 lb cover stock")
        self.assertEqual(self.matcher.best_match("500 sheets of shiny glossy sheets"), "Glossy paper")

    def test_dissimilar_description_matches_nothing(self):
        self.assertIsNone(self.matcher.best_match("rubber bands"))

    def test_shortlist_blocks_lexically_similar_but_semantically_far_items(self):
        # "paper" overlaps lexically with Paper cups, but the embedding shortlist is about cards
        self.assertNotEqual(self.matcher.best_match("heavy card paper"), "Paper cups")

    def test_embeddings_are_cached(self):
        self.matcher.best_match("heavy card for covers")
        calls = len(self.embed.texts)
        self.matcher.best_match("heavy card for covers")
        self.assertEqual(len(self.embed.texts), calls)

    def test_falls_back_to_lexical_matcher_when_embedding_fails(self):
        def broken(texts):
            raise ConnectionError("embeddings API unavailable")
        matcher = HybridCatalogMatcher(CATALOG, broken)
        self.assertEqual(matcher.best_match("colorful cardstock"), matcher.lexical.best_match("colorful cardstock"))
        self.assertEqual(matcher.fallbacks, 1)


if __name__ == "__main__":
    unittest.main()
