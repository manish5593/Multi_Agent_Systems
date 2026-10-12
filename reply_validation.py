"""Check the customer reply against the sales actually recorded for the request.

Pure logic: callers pass in what was sold and which lines were partial.
"""
import re
from typing import Dict, List, Tuple

# (item name, quantity, line total) for each sale recorded in the request
Sale = Tuple[str, int, float]

MAX_REPLY_REWRITES = 2

CONFIRMATION_PATTERN = re.compile(
    r"would you like to proceed|like to proceed|please confirm|confirm (?:if|whether|that you)|"
    r"let (?:me|us) know if you(?:'d| would) like (?:to|us to) (?:proceed|go ahead|continue)",
    re.IGNORECASE,
)
ORDER_PLACED_PATTERN = re.compile(
    r"successfully (?:placed|processed|recorded|finalized)|(?:order|sale) (?:has been|is) "
    r"(?:placed|confirmed|recorded|processed)",
    re.IGNORECASE,
)
INTERNAL_DETAIL_PATTERN = re.compile(
    r"\bcash\b|\bfunds?\b|\bmarkup\b|\bmargin\b|supplier cost|restock(?:ing)? cost|\d[\d,]* (?:units|sheets) in stock|"
    r"\d[\d,]* (?:units|sheets) (?:were|was) available|minimum (?:for a partial order|threshold)|"
    r"\b(?:inventory_agent|quoting_agent|sales_agent|check_availability|price_line_item|record_sale)\b",
    re.IGNORECASE,
)


def reply_requirements(sold: List[Sale], partial: Dict[str, int]) -> str:
    """Everything the reply must say about this request's sales, so a rewrite can't fix one point and drop another."""
    if not sold:
        return "Nothing was sold, so the reply must not say an order was placed or confirmed."
    lines = []
    for name, qty, line_total in sold:
        requested = partial.get(name)
        if requested:
            lines.append(f"{qty} of the {requested:,} requested {name} for ${line_total:,.2f} (the rest is "
                         f"unavailable by the deadline)")
        else:
            lines.append(f"{qty} {name} for ${line_total:,.2f}")
    total = sum(line_total for _, _, line_total in sold)
    return (f"The reply must list these sold items: {'; '.join(lines)}; state the total of ${total:,.2f}; "
            f"not ask the customer to confirm or proceed, because the sale is already recorded; and not "
            f"mention cash, markup, costs, stock counts, the partial-order minimum or internal agents.")


def reply_problems(reply: str, sold: List[Sale], partial: Dict[str, int]) -> List[str]:
    """Check the customer reply against what was actually recorded during the request."""
    problems = []
    numbers = reply.replace(",", "")
    if sold:
        total = sum(line_total for _, _, line_total in sold)
        if f"{total:.2f}" not in numbers:
            items = "; ".join(f"{qty} x {name} ${line_total:.2f}" for name, qty, line_total in sold)
            problems.append(f"State the total of ${total:,.2f} for the items sold ({items}).")
        if CONFIRMATION_PATTERN.search(reply):
            problems.append("The sale is already recorded, so do not ask the customer to confirm or whether to proceed.")
        for name, qty, _ in sold:
            requested = partial.get(name)
            if requested and str(requested) not in numbers:
                problems.append(f"Say that {qty} of the {requested:,} requested {name} will be supplied, "
                                f"and that the rest is unavailable by the deadline.")
    elif ORDER_PLACED_PATTERN.search(reply):
        problems.append("No sale was recorded, so do not say the order was placed or confirmed.")
    leaked = sorted({m.group(0).lower() for m in INTERNAL_DETAIL_PATTERN.finditer(reply)})
    if leaked:
        problems.append(f"Remove internal details: {', '.join(leaked)}.")
    return problems
