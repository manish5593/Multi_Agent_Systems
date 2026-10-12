"""Compare the lexical and hybrid (embedding) catalog matchers on labeled descriptions.

Calls the embeddings API. Run with `python evaluate_matching.py`. The tuning in
catalog_ranking.py used the sample wording plus the even-indexed paraphrases and negatives;
the odd-indexed ones are the held-out half.
"""
SAMPLE = {  # wording from the sample requests (the current matcher gets these right)
    "A4 glossy paper": "Glossy paper", "heavy cardstock (white)": "Cardstock", "colored paper (assorted colors)": "Colored paper",
    "colorful poster paper": "Poster paper", "streamers": "Party streamers", "A4 paper": "A4 paper", "printer paper": "Standard copy paper",
    "A4 size printer paper": "A4 paper", "cardstock in various colors": "Cardstock",
    "decorative washi tape": "Decorative adhesive tape (washi tape)", "colorful construction paper": "Construction paper",
    "white printer paper": "Standard copy paper", "glossy A4 paper": "Glossy paper", 'poster boards (24" x 36")': "Large poster paper (24x36 inches)",
    "heavyweight cardstock": "Cardstock", "A4 matte paper": "Matte paper", "A4 recycled paper": "Recycled paper",
    "A4 white printer paper": "A4 paper", "100% recycled kraft paper envelopes": "Envelopes", "high-quality glossy paper": "Glossy paper",
    "sturdy cardstock": "Cardstock", "colorful cardstock": "Cardstock", "standard printer paper": "Standard copy paper",
    "paper napkins": "Paper napkins", "A4 printing paper": "A4 paper", "poster paper in various colors": "Poster paper",
    "A4 white paper": "A4 paper", "A4 printer paper": "A4 paper", "table napkins (white)": "Paper napkins",
    "paper cups (biodegradable)": "Paper cups", "paper plates (biodegradable)": "Paper plates", "high-quality white cardstock": "Cardstock",
    "standard printing paper": "Standard copy paper", "colored paper in assorted colors": "Colored paper", "flyers": "Flyers",
    "posters": "Poster paper", "250,000 sheets of printer paper": "Standard copy paper", "200 sheets of A4 glossy paper": "Glossy paper",
    "220 gsm poster paper": "220 gsm poster paper", "250 gsm cardstock": "250 gsm cardstock", "100 lb cover stock": "100 lb cover stock",
}
PARAPHRASE = {  # wording the sample requests don't use
    "heavy card stock": "Cardstock", "card stock sheets": "Cardstock", "letter paper": "Letter-sized paper",
    "8.5x11 paper": "Letter-sized paper", "legal paper": "Legal-size paper", "post-it notes": "Sticky notes",
    "sticky pads": "Sticky notes", "name badges with lanyards": "Name tags with lanyards", "lanyard badges": "Name tags with lanyards",
    "folders for presentations": "Presentation folders", "party favor bags": "Paper party bags", "gift wrap": "Wrapping paper",
    "photo printing paper": "Photo paper", "brown kraft paper": "Kraft paper", "environmentally friendly paper": "Eco-friendly paper",
    "sparkly paper": "Glitter paper", "tablecloths": "Table covers", "writing pads": "Notepads", "leaflets": "Flyers",
    "handouts": "Flyers", "invitations": "Invitation cards", "butcher block paper": "Butcher paper",
    "36 inch banner rolls": "Rolls of banner paper (36-inch width)", "washi tape": "Decorative adhesive tape (washi tape)",
    "masking tape with patterns": "Decorative adhesive tape (washi tape)", "tissue streamers": "Party streamers",
    "dinner napkins": "Paper napkins", "coffee cups": "Paper cups", "letterhead stationery": "Letterhead paper",
    "scrapbook paper with patterns": "Patterned paper", "neon paper": "Bright-colored paper",
}
NEGATIVE = [  # things we don't sell; must match nothing
    "balloons", "tickets", "cardboard for signage", "A3 paper", "A5 colored paper", "ballpoint pens", "staplers",
    "ink cartridges", "paper clips", "glue sticks", "scissors", "whiteboard markers", "laminating pouches",
    "candles", "rubber bands", "packing boxes",
]


def main():
    from project_starter import catalog_matcher  # the hybrid matcher, using the real embeddings API

    lexical = catalog_matcher.lexical
    groups = {
        "sample wording": dict(SAMPLE),
        "paraphrases": dict(PARAPHRASE),
        "not sold": {d: None for d in NEGATIVE},
        "held-out half": {**{d: PARAPHRASE[d] for d in list(PARAPHRASE)[1::2]}, **{d: None for d in NEGATIVE[1::2]}},
    }
    print(f"{'':16} {'lexical':>9} {'hybrid':>9}")
    for group, cases in groups.items():
        lex = sum(lexical.best_match(d) == expected for d, expected in cases.items())
        hyb = sum(catalog_matcher.best_match(d) == expected for d, expected in cases.items())
        print(f"{group:16} {lex:>4}/{len(cases):<4} {hyb:>4}/{len(cases):<4}")
    print("\nHybrid mistakes:")
    for d, expected in {**SAMPLE, **PARAPHRASE, **{n: None for n in NEGATIVE}}.items():
        got = catalog_matcher.best_match(d)
        if got != expected:
            print(f"  {d!r} -> {got!r} (expected {expected!r})")
    if catalog_matcher.fallbacks:
        print(f"\nWARNING: {catalog_matcher.fallbacks} lookups fell back to the lexical matcher (embedding failed).")


if __name__ == "__main__":
    main()
