"""Customer pricing: markup over supplier cost, less bulk discounts.

Pure logic: no database access and no per-request state.
"""
from typing import Dict

# Catalog unit_price is what the supplier charges us; customers pay it plus this markup.
# 25% keeps the largest bulk discount profitable: 1.25 * 0.85 = 1.0625 of cost.
MARKUP_RATE = 0.25
# (minimum quantity, discount rate), checked from largest tier down
BULK_DISCOUNT_TIERS = [(1000, 0.15), (500, 0.10), (100, 0.05), (0, 0.0)]


def bulk_discount_rate(quantity: int) -> float:
    for min_quantity, rate in BULK_DISCOUNT_TIERS:
        if quantity >= min_quantity:
            return rate
    return 0.0


def list_price(unit_cost: float) -> float:
    """Customer price per unit before any discount."""
    return round(unit_cost * (1 + MARKUP_RATE), 4)


def price_line(item_name: str, unit_cost: float, quantity: int) -> Dict:
    """Price one line with the bulk discount. Used by both quoting and sales so they always agree."""
    unit_price = list_price(unit_cost)
    discount_rate = bulk_discount_rate(quantity)
    discounted_unit_price = unit_price * (1 - discount_rate)
    return {
        "item_name": item_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "discount_rate": discount_rate,
        "discounted_unit_price": round(discounted_unit_price, 4),
        "line_total": round(discounted_unit_price * quantity, 2),
    }
