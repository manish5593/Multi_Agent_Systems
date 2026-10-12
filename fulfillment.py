"""Decide whether, and how much of, an order can be ready by the customer's deadline.

Pure logic: the caller passes in the item's stock position and the supplier lead-time function,
so nothing here touches the database.
"""
from dataclasses import dataclass
from typing import Callable, Dict

# Largest order size in each supplier lead-time tier of get_supplier_delivery_date
# (<=10 units same day, <=100 one day, <=1000 four days), largest first.
SUPPLIER_ORDER_SIZE_TIERS = [1000, 100, 10]
# A partial line is only sold if at least this share of the requested quantity can be ready in time
MIN_PARTIAL_FRACTION = 0.5

# (order date "YYYY-MM-DD", order quantity) -> delivery date "YYYY-MM-DD"
DeliveryDateFn = Callable[[str, int], str]


@dataclass
class StockPosition:
    """An item's stock and the company's cash on the order date."""
    stock: int
    min_stock_level: int
    unit_cost: float
    cash: float


def plan_fulfillment(quantity: int, position: StockPosition, order_date: str, deadline: str,
                     delivery_date_for: DeliveryDateFn) -> Dict:
    """
    Work out whether `quantity` can be ready by the deadline, and what supplier order (if any)
    that needs. Read-only: nothing is bought here.
    """
    if position.stock >= quantity:
        return {"available": True, "reorder_quantity": 0, "cost": 0.0, "ready_date": order_date}

    # Order enough to cover the shortfall and get back up to the minimum stock level
    reorder_quantity = quantity - position.stock + position.min_stock_level
    delivery_date = delivery_date_for(order_date, reorder_quantity)
    if delivery_date > deadline:
        return {
            "available": False,
            "reason": f"Not enough in stock, and the earliest supplier delivery is {delivery_date}, "
                      f"after the {deadline} deadline.",
        }
    cost = reorder_quantity * position.unit_cost
    if cost > position.cash:
        return {"available": False, "reason": "Not enough in stock and it cannot be restocked at this time."}
    return {"available": True, "reorder_quantity": reorder_quantity, "cost": cost, "ready_date": delivery_date}


def plan_partial(quantity: int, position: StockPosition, order_date: str, deadline: str,
                 delivery_date_for: DeliveryDateFn) -> Dict:
    """
    When the full quantity cannot be ready by the deadline, find the most that can: current
    stock plus the largest affordable supplier order that still arrives in time, keeping the
    minimum stock level as a buffer.
    """
    affordable = int(position.cash // position.unit_cost)
    best_quantity, ready_date = min(position.stock, quantity), order_date
    for tier in SUPPLIER_ORDER_SIZE_TIERS:
        reorder_quantity = min(tier, affordable)
        if reorder_quantity <= 0:
            continue
        delivery_date = delivery_date_for(order_date, reorder_quantity)
        if delivery_date > deadline:
            continue
        with_reorder = min(quantity, position.stock + reorder_quantity - position.min_stock_level)
        if with_reorder > best_quantity:
            best_quantity, ready_date = with_reorder, delivery_date
        break  # tiers are largest first, so the first one that arrives in time supplies the most
    return {"quantity": best_quantity, "ready_date": ready_date}


def meets_partial_minimum(available_quantity: int, requested_quantity: int) -> bool:
    return available_quantity >= MIN_PARTIAL_FRACTION * requested_quantity
