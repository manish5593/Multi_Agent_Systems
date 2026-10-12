"""Tests for validate_results.py: each check must pass on good results and catch the problem it targets.

Run with `python -m unittest test_validate_results`.
"""
import os
import tempfile
import unittest

import pandas as pd

from validate_results import check_results

RESULTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_results.csv")


class CheckResultsTest(unittest.TestCase):
    def setUp(self):
        self.df = pd.read_csv(RESULTS)
        self.sold_row = self.df.index[0]  # request 1 sold items
        no_sale = self.df[self.df["cash_balance"].diff().abs() < 0.005]
        self.no_sale_row = no_sale.index[0]

    def failures_for(self, df):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            path = f.name
        try:
            df.to_csv(path, index=False)
            return check_results(path)
        finally:
            os.unlink(path)

    def assertCaught(self, df, phrase):
        failures = self.failures_for(df)
        self.assertTrue(any(phrase in f for f in failures), f"expected a failure containing {phrase!r}, got {failures}")

    def test_committed_results_pass(self):
        self.assertEqual(check_results(RESULTS), [])

    def test_internal_details_are_caught(self):
        for leak in ("Our cash position is strong.", "Only 865 sheets were available.",
                     "That is below the minimum for a partial order.", "The sales_agent recorded it."):
            df = self.df.copy()
            df.loc[self.sold_row, "response"] += " " + leak
            self.assertCaught(df, "internal details")

    def test_failed_request_is_caught(self):
        df = self.df.copy()
        df.loc[self.no_sale_row, "response"] = "Sorry, we could not process your request right now. Please try again later."
        self.assertCaught(df, "fallback reply")

    def test_row_without_sale_or_reason_is_caught(self):
        df = self.df.copy()
        df.loc[self.no_sale_row, "response"] = "Thank you for contacting Munder Difflin."
        self.assertCaught(df, "neither a sale nor a reason")

    def test_sale_without_price_is_caught(self):
        df = self.df.copy()
        df.loc[self.sold_row, "response"] = "Your order is on its way."
        self.assertCaught(df, "states no price")

    def test_confirmation_after_sale_is_caught(self):
        df = self.df.copy()
        df.loc[self.sold_row, "response"] += " Would you like to proceed?"
        self.assertCaught(df, "asks the customer to confirm")

    def test_order_claimed_without_sale_is_caught(self):
        df = self.df.copy()
        df.loc[self.no_sale_row, "response"] += " Your order has been placed."
        self.assertCaught(df, "says the order was placed")

    def test_falling_assets_are_caught(self):
        df = self.df.copy()
        df.loc[self.sold_row, "cash_balance"] -= 500  # as if a sale lost money
        self.assertCaught(df, "total assets fell")

    def test_negative_balance_is_caught(self):
        df = self.df.copy()
        df.loc[self.sold_row, "inventory_value"] = -1
        self.assertCaught(df, "negative cash or inventory")

    def test_file_shape_is_checked(self):
        self.assertCaught(self.df.iloc[:-1], "Expected 20 rows")
        self.assertCaught(pd.concat([self.df.iloc[:-1], self.df.iloc[[0]]]), "Duplicate request_ids")
        self.assertCaught(self.df.iloc[::-1], "not in request_date order")


if __name__ == "__main__":
    unittest.main()
