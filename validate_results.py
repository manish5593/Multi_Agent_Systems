"""Automated checks on test_results.csv.

These are properties every run must satisfy, rather than one run's exact wording, which varies
from run to run. Run standalone with `python validate_results.py [path]`; it exits with status 1
if any check fails. run_test_scenarios() also calls it after writing the results.
"""
import re
import sys
from typing import List, Union

import pandas as pd

from reply_validation import CONFIRMATION_PATTERN, INTERNAL_DETAIL_PATTERN, ORDER_PLACED_PATTERN

# Starting position created by the starter's init_database(seed=137), used when the caller
# doesn't pass the real one: $50,000 opening cash minus the cost of the seeded stock.
DEFAULT_STARTING_CASH = 45059.70
DEFAULT_STARTING_INVENTORY = 4940.30
EXPECTED_REQUESTS = 20
CENTS = 0.005

# The fallback reply run_test_scenarios() uses when the agent system raises (e.g. an API outage)
FAILURE_REPLY = "could not process your request"
PRICE_PATTERN = re.compile(r"\$\s?\d")
NON_FULFILLMENT_PATTERN = re.compile(
    r"unavailable|not available|n[o']t (?:something )?(?:we )?carr(?:y|ied)|do not carry|don't carry|"
    r"not in our (?:catalog|inventory)|(?:can(?:not|'t)|could not) (?:be )?(?:suppl|deliver|fulfill)|"
    r"miss(?:es)? (?:your|the) (?:deadline|requested date)|after (?:your|the) (?:deadline|requested date)|"
    r"unable to (?:supply|fulfill|provide)|only \d[\d,]* (?:of|sheets|units)|of the \d[\d,]* requested",
    re.IGNORECASE,
)


def check_results(path: str = "test_results.csv",
                  starting_cash: float = DEFAULT_STARTING_CASH,
                  starting_inventory: float = DEFAULT_STARTING_INVENTORY) -> List[str]:
    """Return a list of failed checks; an empty list means every check passed."""
    df = pd.read_csv(path)
    failures = []

    # File shape
    if len(df) != EXPECTED_REQUESTS:
        failures.append(f"Expected {EXPECTED_REQUESTS} rows, found {len(df)}.")
    if df["request_id"].duplicated().any():
        failures.append(f"Duplicate request_ids: {sorted(df.loc[df['request_id'].duplicated(), 'request_id'])}.")
    if list(df["request_date"]) != sorted(df["request_date"]):
        failures.append("Rows are not in request_date order.")

    previous_cash, previous_assets = starting_cash, starting_cash + starting_inventory
    for row in df.itertuples():
        request = f"Request {row.request_id}"
        response = str(row.response)
        sold = abs(row.cash_balance - previous_cash) > CENTS
        assets = row.cash_balance + row.inventory_value

        if FAILURE_REPLY in response:
            failures.append(f"{request}: the agent system failed and returned the fallback reply.")
        leaked = sorted({m.group(0).lower() for m in INTERNAL_DETAIL_PATTERN.finditer(response)})
        if leaked:
            failures.append(f"{request}: response contains internal details: {', '.join(leaked)}.")

        has_price = bool(PRICE_PATTERN.search(response))
        has_reason = bool(NON_FULFILLMENT_PATTERN.search(response))
        if not (sold and has_price) and not has_reason:
            failures.append(f"{request}: response includes neither a sale nor a reason for non-fulfillment.")
        if sold and not has_price:
            failures.append(f"{request}: cash changed but the response states no price.")
        if sold and CONFIRMATION_PATTERN.search(response):
            failures.append(f"{request}: the sale was recorded but the response asks the customer to confirm.")
        if not sold and ORDER_PLACED_PATTERN.search(response):
            failures.append(f"{request}: nothing was sold but the response says the order was placed.")

        if row.cash_balance < 0 or row.inventory_value < 0:
            failures.append(f"{request}: negative cash or inventory value.")
        # Every sale is priced above cost and restocking only turns cash into inventory,
        # so total assets should never fall from one request to the next.
        if assets < previous_assets - CENTS:
            failures.append(f"{request}: total assets fell from ${previous_assets:,.2f} to ${assets:,.2f}.")
        previous_cash, previous_assets = row.cash_balance, assets
    return failures


def report(failures: List[str], path: str) -> None:
    if failures:
        print(f"RESULT CHECKS FAILED for {path} ({len(failures)}):")
        for failure in failures:
            print(f"  - {failure}")
    else:
        print(f"RESULT CHECKS PASSED for {path}")


if __name__ == "__main__":
    results_path = sys.argv[1] if len(sys.argv) > 1 else "test_results.csv"
    problems = check_results(results_path)
    report(problems, results_path)
    sys.exit(1 if problems else 0)
