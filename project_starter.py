import pandas as pd
import numpy as np
import os
import time
import dotenv
import ast
from sqlalchemy.sql import text
from datetime import datetime, timedelta
from typing import Dict, List, Union
from sqlalchemy import create_engine, Engine

# Create an SQLite database
db_engine = create_engine("sqlite:///munder_difflin.db")

# List containing the different kinds of papers 
paper_supplies = [
    # Paper Types (priced per sheet unless specified)
    {"item_name": "A4 paper",                         "category": "paper",        "unit_price": 0.05},
    {"item_name": "Letter-sized paper",              "category": "paper",        "unit_price": 0.06},
    {"item_name": "Cardstock",                        "category": "paper",        "unit_price": 0.15},
    {"item_name": "Colored paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Glossy paper",                     "category": "paper",        "unit_price": 0.20},
    {"item_name": "Matte paper",                      "category": "paper",        "unit_price": 0.18},
    {"item_name": "Recycled paper",                   "category": "paper",        "unit_price": 0.08},
    {"item_name": "Eco-friendly paper",               "category": "paper",        "unit_price": 0.12},
    {"item_name": "Poster paper",                     "category": "paper",        "unit_price": 0.25},
    {"item_name": "Banner paper",                     "category": "paper",        "unit_price": 0.30},
    {"item_name": "Kraft paper",                      "category": "paper",        "unit_price": 0.10},
    {"item_name": "Construction paper",               "category": "paper",        "unit_price": 0.07},
    {"item_name": "Wrapping paper",                   "category": "paper",        "unit_price": 0.15},
    {"item_name": "Glitter paper",                    "category": "paper",        "unit_price": 0.22},
    {"item_name": "Decorative paper",                 "category": "paper",        "unit_price": 0.18},
    {"item_name": "Letterhead paper",                 "category": "paper",        "unit_price": 0.12},
    {"item_name": "Legal-size paper",                 "category": "paper",        "unit_price": 0.08},
    {"item_name": "Crepe paper",                      "category": "paper",        "unit_price": 0.05},
    {"item_name": "Photo paper",                      "category": "paper",        "unit_price": 0.25},
    {"item_name": "Uncoated paper",                   "category": "paper",        "unit_price": 0.06},
    {"item_name": "Butcher paper",                    "category": "paper",        "unit_price": 0.10},
    {"item_name": "Heavyweight paper",                "category": "paper",        "unit_price": 0.20},
    {"item_name": "Standard copy paper",              "category": "paper",        "unit_price": 0.04},
    {"item_name": "Bright-colored paper",             "category": "paper",        "unit_price": 0.12},
    {"item_name": "Patterned paper",                  "category": "paper",        "unit_price": 0.15},

    # Product Types (priced per unit)
    {"item_name": "Paper plates",                     "category": "product",      "unit_price": 0.10},  # per plate
    {"item_name": "Paper cups",                       "category": "product",      "unit_price": 0.08},  # per cup
    {"item_name": "Paper napkins",                    "category": "product",      "unit_price": 0.02},  # per napkin
    {"item_name": "Disposable cups",                  "category": "product",      "unit_price": 0.10},  # per cup
    {"item_name": "Table covers",                     "category": "product",      "unit_price": 1.50},  # per cover
    {"item_name": "Envelopes",                        "category": "product",      "unit_price": 0.05},  # per envelope
    {"item_name": "Sticky notes",                     "category": "product",      "unit_price": 0.03},  # per sheet
    {"item_name": "Notepads",                         "category": "product",      "unit_price": 2.00},  # per pad
    {"item_name": "Invitation cards",                 "category": "product",      "unit_price": 0.50},  # per card
    {"item_name": "Flyers",                           "category": "product",      "unit_price": 0.15},  # per flyer
    {"item_name": "Party streamers",                  "category": "product",      "unit_price": 0.05},  # per roll
    {"item_name": "Decorative adhesive tape (washi tape)", "category": "product", "unit_price": 0.20},  # per roll
    {"item_name": "Paper party bags",                 "category": "product",      "unit_price": 0.25},  # per bag
    {"item_name": "Name tags with lanyards",          "category": "product",      "unit_price": 0.75},  # per tag
    {"item_name": "Presentation folders",             "category": "product",      "unit_price": 0.50},  # per folder

    # Large-format items (priced per unit)
    {"item_name": "Large poster paper (24x36 inches)", "category": "large_format", "unit_price": 1.00},
    {"item_name": "Rolls of banner paper (36-inch width)", "category": "large_format", "unit_price": 2.50},

    # Specialty papers
    {"item_name": "100 lb cover stock",               "category": "specialty",    "unit_price": 0.50},
    {"item_name": "80 lb text paper",                 "category": "specialty",    "unit_price": 0.40},
    {"item_name": "250 gsm cardstock",                "category": "specialty",    "unit_price": 0.30},
    {"item_name": "220 gsm poster paper",             "category": "specialty",    "unit_price": 0.35},
]

# Given below are some utility functions you can use to implement your multi-agent system

def generate_sample_inventory(paper_supplies: list, coverage: float = 0.4, seed: int = 137) -> pd.DataFrame:
    """
    Generate inventory for exactly a specified percentage of items from the full paper supply list.

    This function randomly selects exactly `coverage` × N items from the `paper_supplies` list,
    and assigns each selected item:
    - a random stock quantity between 200 and 800,
    - a minimum stock level between 50 and 150.

    The random seed ensures reproducibility of selection and stock levels.

    Args:
        paper_supplies (list): A list of dictionaries, each representing a paper item with
                               keys 'item_name', 'category', and 'unit_price'.
        coverage (float, optional): Fraction of items to include in the inventory (default is 0.4, or 40%).
        seed (int, optional): Random seed for reproducibility (default is 137).

    Returns:
        pd.DataFrame: A DataFrame with the selected items and assigned inventory values, including:
                      - item_name
                      - category
                      - unit_price
                      - current_stock
                      - min_stock_level
    """
    # Ensure reproducible random output
    np.random.seed(seed)

    # Calculate number of items to include based on coverage
    num_items = int(len(paper_supplies) * coverage)

    # Randomly select item indices without replacement
    selected_indices = np.random.choice(
        range(len(paper_supplies)),
        size=num_items,
        replace=False
    )

    # Extract selected items from paper_supplies list
    selected_items = [paper_supplies[i] for i in selected_indices]

    # Construct inventory records
    inventory = []
    for item in selected_items:
        inventory.append({
            "item_name": item["item_name"],
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": np.random.randint(200, 800),  # Realistic stock range
            "min_stock_level": np.random.randint(50, 150)  # Reasonable threshold for reordering
        })

    # Return inventory as a pandas DataFrame
    return pd.DataFrame(inventory)

def init_database(db_engine: Engine, seed: int = 137) -> Engine:    
    """
    Set up the Munder Difflin database with all required tables and initial records.

    This function performs the following tasks:
    - Creates the 'transactions' table for logging stock orders and sales
    - Loads customer inquiries from 'quote_requests.csv' into a 'quote_requests' table
    - Loads previous quotes from 'quotes.csv' into a 'quotes' table, extracting useful metadata
    - Generates a random subset of paper inventory using `generate_sample_inventory`
    - Inserts initial financial records including available cash and starting stock levels

    Args:
        db_engine (Engine): A SQLAlchemy engine connected to the SQLite database.
        seed (int, optional): A random seed used to control reproducibility of inventory stock levels.
                              Default is 137.

    Returns:
        Engine: The same SQLAlchemy engine, after initializing all necessary tables and records.

    Raises:
        Exception: If an error occurs during setup, the exception is printed and raised.
    """
    try:
        # ----------------------------
        # 1. Create an empty 'transactions' table schema
        # ----------------------------
        transactions_schema = pd.DataFrame({
            "id": [],
            "item_name": [],
            "transaction_type": [],  # 'stock_orders' or 'sales'
            "units": [],             # Quantity involved
            "price": [],             # Total price for the transaction
            "transaction_date": [],  # ISO-formatted date
        })
        transactions_schema.to_sql("transactions", db_engine, if_exists="replace", index=False)

        # Set a consistent starting date
        initial_date = datetime(2025, 1, 1).isoformat()

        # ----------------------------
        # 2. Load and initialize 'quote_requests' table
        # ----------------------------
        quote_requests_df = pd.read_csv("quote_requests.csv")
        quote_requests_df["id"] = range(1, len(quote_requests_df) + 1)
        quote_requests_df.to_sql("quote_requests", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 3. Load and transform 'quotes' table
        # ----------------------------
        quotes_df = pd.read_csv("quotes.csv")
        quotes_df["request_id"] = range(1, len(quotes_df) + 1)
        quotes_df["order_date"] = initial_date

        # Unpack metadata fields (job_type, order_size, event_type) if present
        if "request_metadata" in quotes_df.columns:
            quotes_df["request_metadata"] = quotes_df["request_metadata"].apply(
                lambda x: ast.literal_eval(x) if isinstance(x, str) else x
            )
            quotes_df["job_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("job_type", ""))
            quotes_df["order_size"] = quotes_df["request_metadata"].apply(lambda x: x.get("order_size", ""))
            quotes_df["event_type"] = quotes_df["request_metadata"].apply(lambda x: x.get("event_type", ""))

        # Retain only relevant columns
        quotes_df = quotes_df[[
            "request_id",
            "total_amount",
            "quote_explanation",
            "order_date",
            "job_type",
            "order_size",
            "event_type"
        ]]
        quotes_df.to_sql("quotes", db_engine, if_exists="replace", index=False)

        # ----------------------------
        # 4. Generate inventory and seed stock
        # ----------------------------
        inventory_df = generate_sample_inventory(paper_supplies, seed=seed)

        # Seed initial transactions
        initial_transactions = []

        # Add a starting cash balance via a dummy sales transaction
        initial_transactions.append({
            "item_name": None,
            "transaction_type": "sales",
            "units": None,
            "price": 50000.0,
            "transaction_date": initial_date,
        })

        # Add one stock order transaction per inventory item
        for _, item in inventory_df.iterrows():
            initial_transactions.append({
                "item_name": item["item_name"],
                "transaction_type": "stock_orders",
                "units": item["current_stock"],
                "price": item["current_stock"] * item["unit_price"],
                "transaction_date": initial_date,
            })

        # Commit transactions to database
        pd.DataFrame(initial_transactions).to_sql("transactions", db_engine, if_exists="append", index=False)

        # Save the inventory reference table
        inventory_df.to_sql("inventory", db_engine, if_exists="replace", index=False)

        return db_engine

    except Exception as e:
        print(f"Error initializing database: {e}")
        raise

def create_transaction(
    item_name: str,
    transaction_type: str,
    quantity: int,
    price: float,
    date: Union[str, datetime],
) -> int:
    """
    This function records a transaction of type 'stock_orders' or 'sales' with a specified
    item name, quantity, total price, and transaction date into the 'transactions' table of the database.

    Args:
        item_name (str): The name of the item involved in the transaction.
        transaction_type (str): Either 'stock_orders' or 'sales'.
        quantity (int): Number of units involved in the transaction.
        price (float): Total price of the transaction.
        date (str or datetime): Date of the transaction in ISO 8601 format.

    Returns:
        int: The ID of the newly inserted transaction.

    Raises:
        ValueError: If `transaction_type` is not 'stock_orders' or 'sales'.
        Exception: For other database or execution errors.
    """
    try:
        # Convert datetime to ISO string if necessary
        date_str = date.isoformat() if isinstance(date, datetime) else date

        # Validate transaction type
        if transaction_type not in {"stock_orders", "sales"}:
            raise ValueError("Transaction type must be 'stock_orders' or 'sales'")

        # Prepare transaction record as a single-row DataFrame
        transaction = pd.DataFrame([{
            "item_name": item_name,
            "transaction_type": transaction_type,
            "units": quantity,
            "price": price,
            "transaction_date": date_str,
        }])

        # Insert the record into the database
        transaction.to_sql("transactions", db_engine, if_exists="append", index=False)

        # Fetch and return the ID of the inserted row
        result = pd.read_sql("SELECT last_insert_rowid() as id", db_engine)
        return int(result.iloc[0]["id"])

    except Exception as e:
        print(f"Error creating transaction: {e}")
        raise

def get_all_inventory(as_of_date: str) -> Dict[str, int]:
    """
    Retrieve a snapshot of available inventory as of a specific date.

    This function calculates the net quantity of each item by summing 
    all stock orders and subtracting all sales up to and including the given date.

    Only items with positive stock are included in the result.

    Args:
        as_of_date (str): ISO-formatted date string (YYYY-MM-DD) representing the inventory cutoff.

    Returns:
        Dict[str, int]: A dictionary mapping item names to their current stock levels.
    """
    # SQL query to compute stock levels per item as of the given date
    query = """
        SELECT
            item_name,
            SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END) as stock
        FROM transactions
        WHERE item_name IS NOT NULL
        AND transaction_date <= :as_of_date
        GROUP BY item_name
        HAVING stock > 0
    """

    # Execute the query with the date parameter
    result = pd.read_sql(query, db_engine, params={"as_of_date": as_of_date})

    # Convert the result into a dictionary {item_name: stock}
    return dict(zip(result["item_name"], result["stock"]))

def get_stock_level(item_name: str, as_of_date: Union[str, datetime]) -> pd.DataFrame:
    """
    Retrieve the stock level of a specific item as of a given date.

    This function calculates the net stock by summing all 'stock_orders' and 
    subtracting all 'sales' transactions for the specified item up to the given date.

    Args:
        item_name (str): The name of the item to look up.
        as_of_date (str or datetime): The cutoff date (inclusive) for calculating stock.

    Returns:
        pd.DataFrame: A single-row DataFrame with columns 'item_name' and 'current_stock'.
    """
    # Convert date to ISO string format if it's a datetime object
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # SQL query to compute net stock level for the item
    stock_query = """
        SELECT
            item_name,
            COALESCE(SUM(CASE
                WHEN transaction_type = 'stock_orders' THEN units
                WHEN transaction_type = 'sales' THEN -units
                ELSE 0
            END), 0) AS current_stock
        FROM transactions
        WHERE item_name = :item_name
        AND transaction_date <= :as_of_date
    """

    # Execute query and return result as a DataFrame
    return pd.read_sql(
        stock_query,
        db_engine,
        params={"item_name": item_name, "as_of_date": as_of_date},
    )

def get_supplier_delivery_date(input_date_str: str, quantity: int) -> str:
    """
    Estimate the supplier delivery date based on the requested order quantity and a starting date.

    Delivery lead time increases with order size:
        - ≤10 units: same day
        - 11–100 units: 1 day
        - 101–1000 units: 4 days
        - >1000 units: 7 days

    Args:
        input_date_str (str): The starting date in ISO format (YYYY-MM-DD).
        quantity (int): The number of units in the order.

    Returns:
        str: Estimated delivery date in ISO format (YYYY-MM-DD).
    """
    # Debug log (comment out in production if needed)
    print(f"FUNC (get_supplier_delivery_date): Calculating for qty {quantity} from date string '{input_date_str}'")

    # Attempt to parse the input date
    try:
        input_date_dt = datetime.fromisoformat(input_date_str.split("T")[0])
    except (ValueError, TypeError):
        # Fallback to current date on format error
        print(f"WARN (get_supplier_delivery_date): Invalid date format '{input_date_str}', using today as base.")
        input_date_dt = datetime.now()

    # Determine delivery delay based on quantity
    if quantity <= 10:
        days = 0
    elif quantity <= 100:
        days = 1
    elif quantity <= 1000:
        days = 4
    else:
        days = 7

    # Add delivery days to the starting date
    delivery_date_dt = input_date_dt + timedelta(days=days)

    # Return formatted delivery date
    return delivery_date_dt.strftime("%Y-%m-%d")

def get_cash_balance(as_of_date: Union[str, datetime]) -> float:
    """
    Calculate the current cash balance as of a specified date.

    The balance is computed by subtracting total stock purchase costs ('stock_orders')
    from total revenue ('sales') recorded in the transactions table up to the given date.

    Args:
        as_of_date (str or datetime): The cutoff date (inclusive) in ISO format or as a datetime object.

    Returns:
        float: Net cash balance as of the given date. Returns 0.0 if no transactions exist or an error occurs.
    """
    try:
        # Convert date to ISO format if it's a datetime object
        if isinstance(as_of_date, datetime):
            as_of_date = as_of_date.isoformat()

        # Query all transactions on or before the specified date
        transactions = pd.read_sql(
            "SELECT * FROM transactions WHERE transaction_date <= :as_of_date",
            db_engine,
            params={"as_of_date": as_of_date},
        )

        # Compute the difference between sales and stock purchases
        if not transactions.empty:
            total_sales = transactions.loc[transactions["transaction_type"] == "sales", "price"].sum()
            total_purchases = transactions.loc[transactions["transaction_type"] == "stock_orders", "price"].sum()
            return float(total_sales - total_purchases)

        return 0.0

    except Exception as e:
        print(f"Error getting cash balance: {e}")
        return 0.0


def generate_financial_report(as_of_date: Union[str, datetime]) -> Dict:
    """
    Generate a complete financial report for the company as of a specific date.

    This includes:
    - Cash balance
    - Inventory valuation
    - Combined asset total
    - Itemized inventory breakdown
    - Top 5 best-selling products

    Args:
        as_of_date (str or datetime): The date (inclusive) for which to generate the report.

    Returns:
        Dict: A dictionary containing the financial report fields:
            - 'as_of_date': The date of the report
            - 'cash_balance': Total cash available
            - 'inventory_value': Total value of inventory
            - 'total_assets': Combined cash and inventory value
            - 'inventory_summary': List of items with stock and valuation details
            - 'top_selling_products': List of top 5 products by revenue
    """
    # Normalize date input
    if isinstance(as_of_date, datetime):
        as_of_date = as_of_date.isoformat()

    # Get current cash balance
    cash = get_cash_balance(as_of_date)

    # Get current inventory snapshot
    inventory_df = pd.read_sql("SELECT * FROM inventory", db_engine)
    inventory_value = 0.0
    inventory_summary = []

    # Compute total inventory value and summary by item
    for _, item in inventory_df.iterrows():
        stock_info = get_stock_level(item["item_name"], as_of_date)
        stock = stock_info["current_stock"].iloc[0]
        item_value = stock * item["unit_price"]
        inventory_value += item_value

        inventory_summary.append({
            "item_name": item["item_name"],
            "stock": stock,
            "unit_price": item["unit_price"],
            "value": item_value,
        })

    # Identify top-selling products by revenue
    top_sales_query = """
        SELECT item_name, SUM(units) as total_units, SUM(price) as total_revenue
        FROM transactions
        WHERE transaction_type = 'sales' AND transaction_date <= :date
        GROUP BY item_name
        ORDER BY total_revenue DESC
        LIMIT 5
    """
    top_sales = pd.read_sql(top_sales_query, db_engine, params={"date": as_of_date})
    top_selling_products = top_sales.to_dict(orient="records")

    return {
        "as_of_date": as_of_date,
        "cash_balance": cash,
        "inventory_value": inventory_value,
        "total_assets": cash + inventory_value,
        "inventory_summary": inventory_summary,
        "top_selling_products": top_selling_products,
    }


def search_quote_history(search_terms: List[str], limit: int = 5) -> List[Dict]:
    """
    Retrieve a list of historical quotes that match any of the provided search terms.

    The function searches both the original customer request (from `quote_requests`) and
    the explanation for the quote (from `quotes`) for each keyword. Results are sorted by
    most recent order date and limited by the `limit` parameter.

    Args:
        search_terms (List[str]): List of terms to match against customer requests and explanations.
        limit (int, optional): Maximum number of quote records to return. Default is 5.

    Returns:
        List[Dict]: A list of matching quotes, each represented as a dictionary with fields:
            - original_request
            - total_amount
            - quote_explanation
            - job_type
            - order_size
            - event_type
            - order_date
    """
    conditions = []
    params = {}

    # Build SQL WHERE clause using LIKE filters for each search term
    for i, term in enumerate(search_terms):
        param_name = f"term_{i}"
        conditions.append(
            f"(LOWER(qr.response) LIKE :{param_name} OR "
            f"LOWER(q.quote_explanation) LIKE :{param_name})"
        )
        params[param_name] = f"%{term.lower()}%"

    # Combine conditions; fallback to always-true if no terms provided
    where_clause = " AND ".join(conditions) if conditions else "1=1"

    # Final SQL query to join quotes with quote_requests
    query = f"""
        SELECT
            qr.response AS original_request,
            q.total_amount,
            q.quote_explanation,
            q.job_type,
            q.order_size,
            q.event_type,
            q.order_date
        FROM quotes q
        JOIN quote_requests qr ON q.request_id = qr.id
        WHERE {where_clause}
        ORDER BY q.order_date DESC
        LIMIT {limit}
    """

    # Execute parameterized query
    with db_engine.connect() as conn:
        result = conn.execute(text(query), params)
        return [dict(row._mapping) for row in result]

########################
########################
########################
# YOUR MULTI AGENT STARTS HERE
########################
########################
########################


import json
import re
import threading
import openai
from smolagents import OpenAIServerModel, ToolCallingAgent, tool

# Deterministic business logic, kept in small modules next to this file
from fulfillment import StockPosition, meets_partial_minimum, plan_fulfillment, plan_partial, MIN_PARTIAL_FRACTION
from catalog_ranking import HybridCatalogMatcher
from matching import normalize_description
from pricing import price_line
from reply_validation import MAX_REPLY_REWRITES, reply_problems, reply_requirements
from validate_results import check_results, report as report_result_checks

# Set up and load your env parameters and instantiate your model.
dotenv.load_dotenv()

API_BASE = "https://openai.vocareum.com/v1"
model = OpenAIServerModel(
    model_id=os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini"),
    api_base=API_BASE,
    api_key=os.getenv("UDACITY_OPENAI_API_KEY"),
)

# Embeddings for ranking catalog items (see catalog_ranking.py)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
_embedding_client = openai.OpenAI(base_url=API_BASE, api_key=os.getenv("UDACITY_OPENAI_API_KEY"))


def _embed(texts: List[str]) -> List[List[float]]:
    response = _embedding_client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]

# Business rules shared by the tools
CATALOG = {item["item_name"]: item for item in paper_supplies}
catalog_matcher = HybridCatalogMatcher({name: item["category"] for name, item in CATALOG.items()}, _embed)
DEFAULT_MIN_STOCK_LEVEL = 100
# Serializes check-then-write in record_sale so concurrent calls cannot oversell or corrupt SQLite
_db_write_lock = threading.Lock()


# The date and delivery deadline of the request being processed. Set by call_multi_agent_system
# so that every transaction uses the real dates rather than dates chosen by the LLM.
# "approved" maps item name -> quantity confirmed by check_availability; only those can be quoted or sold.
# "matched" maps each customer description checked this request -> the catalog item it matched.
# "partial" maps item name -> requested quantity for lines approved only in part.
# "sold" lists (item name, quantity, line total) for each sale recorded this request.
_request_context = {"date": None, "deadline": None, "approved": {}, "matched": {}, "partial": {}, "sold": []}


def _reset_request_context(date: Union[str, None] = None, deadline: Union[str, None] = None) -> None:
    _request_context.update(date=date, deadline=deadline, approved={}, matched={}, partial={}, sold=[])
DEADLINE_PATTERN = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})"
)


def _request_date() -> str:
    if _request_context["date"] is None:
        raise RuntimeError("No request date set; call call_multi_agent_system().")
    return _request_context["date"]


SHEETS_PER_REAM = 500
REAM_PATTERN = re.compile(r"\b(\d[\d,]*)\s+reams?\b", re.IGNORECASE)


def _convert_reams_to_sheets(request: str) -> str:
    """Rewrite "500 reams" as "250,000 sheets" so every agent works in sheets."""
    def to_sheets(match: re.Match) -> str:
        reams = int(match.group(1).replace(",", ""))
        return f"{reams * SHEETS_PER_REAM:,} sheets"
    return REAM_PATTERN.sub(to_sheets, request)


def _parse_deadline(request: str, request_date: str) -> str:
    """Find the first date like "April 15, 2025" on or after the request date; default to 14 days out."""
    for month, day, year in DEADLINE_PATTERN.findall(request):
        deadline = datetime.strptime(f"{month} {day} {year}", "%B %d %Y").strftime("%Y-%m-%d")
        if deadline >= request_date:
            return deadline
    return (datetime.fromisoformat(request_date) + timedelta(days=14)).strftime("%Y-%m-%d")


def _current_stock(item_name: str, as_of_date: str) -> int:
    return int(get_stock_level(item_name, as_of_date)["current_stock"].iloc[0])


def _min_stock_level(item_name: str) -> int:
    inventory_df = pd.read_sql(
        "SELECT min_stock_level FROM inventory WHERE item_name = :item_name",
        db_engine,
        params={"item_name": item_name},
    )
    if inventory_df.empty:
        return DEFAULT_MIN_STOCK_LEVEL
    return int(inventory_df["min_stock_level"].iloc[0])


def _ensure_in_inventory_table(item_name: str) -> None:
    """Track newly stocked catalog items so the financial report values them."""
    existing = pd.read_sql(
        "SELECT item_name FROM inventory WHERE item_name = :item_name",
        db_engine,
        params={"item_name": item_name},
    )
    if existing.empty:
        item = CATALOG[item_name]
        pd.DataFrame([{
            "item_name": item_name,
            "category": item["category"],
            "unit_price": item["unit_price"],
            "current_stock": 0,
            "min_stock_level": DEFAULT_MIN_STOCK_LEVEL,
        }]).to_sql("inventory", db_engine, if_exists="append", index=False)


def _stock_position(item_name: str) -> StockPosition:
    order_date = _request_date()
    return StockPosition(
        stock=_current_stock(item_name, order_date),
        min_stock_level=_min_stock_level(item_name),
        unit_cost=CATALOG[item_name]["unit_price"],
        cash=get_cash_balance(order_date),
    )


def _plan_fulfillment(item_name: str, quantity: int, position: Union[StockPosition, None] = None) -> Dict:
    return plan_fulfillment(quantity, position or _stock_position(item_name), _request_date(),
                            _request_context["deadline"], get_supplier_delivery_date)


def _price_line(item_name: str, quantity: int) -> Dict:
    return price_line(item_name, CATALOG[item_name]["unit_price"], quantity)


def _resolve_requested_item(name_or_description: str) -> Union[str, None]:
    """
    Map an exact catalog name, a description already checked this request, or a near-miss name
    (e.g. "Washi tape", "A4 matte paper") to its catalog item. Callers still require approval.
    """
    return (catalog_matcher.exact(name_or_description)
            or _request_context["matched"].get(normalize_description(name_or_description))
            or catalog_matcher.best_match(name_or_description))


def _not_approved_error(item: str, quantity: int, action: str) -> str:
    approved = ", ".join(f"{qty} x {name}" for name, qty in _request_context["approved"].items()) or "none"
    return (f"ERROR: {quantity} x {item} was not confirmed by check_availability for this request, so it "
            f"cannot be {action}. Confirmed items: {approved}. Use those exact names and quantities.")


"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""


# Tools for inventory agent

@tool
def list_inventory() -> str:
    """
    List every item in stock on the date of the current request, with its quantity. For internal
    context only: it does not approve anything (use check_availability for that), and stock levels
    must never be quoted to the customer.

    Returns:
        A JSON object mapping catalog item names to units in stock.
    """
    return json.dumps({name: int(units) for name, units in get_all_inventory(_request_date()).items()})


@tool
def check_availability(description: str, quantity: int) -> str:
    """
    Match one requested item to the catalog and check whether the quantity can be ready by the
    customer's deadline, counting current stock and a possible supplier reorder. If only part of
    it can be ready, and at least half, reports how much ("available": "partial"). This only
    checks; it does not buy anything.

    Args:
        description: The customer's wording for one requested item, copied verbatim, e.g. "colorful cardstock".
        quantity: The number of units the customer wants.

    Returns:
        A JSON object with the matched catalog item_name, whether it is available by the deadline
        (true, "partial" or false), the available_quantity, and its ready date or the reason not.
    """
    item_name = catalog_matcher.best_match(description)
    if item_name is None:
        return json.dumps({"description": description, "item_name": None, "available": False,
                           "reason": "Not something we carry."})
    _request_context["matched"][normalize_description(description)] = item_name
    already_sold = sum(qty for name, qty, _ in _request_context["sold"] if name == item_name)
    if already_sold:
        # Re-checking after a sale must not approve the item again, or it could be sold twice
        return json.dumps({"description": description, "item_name": item_name, "available": "already sold",
                           "reason": f"{already_sold} x {item_name} was already sold in this request."})
    position = _stock_position(item_name)
    plan = _plan_fulfillment(item_name, quantity, position)
    result = {"description": description, "item_name": item_name, "quantity": quantity,
              "available": plan["available"]}
    if plan["available"]:
        result["available_quantity"] = quantity
        result["ready_date"] = plan["ready_date"]
        _request_context["approved"][item_name] = quantity
        return json.dumps(result)

    partial = plan_partial(quantity, position, _request_date(), _request_context["deadline"],
                           get_supplier_delivery_date)
    if partial["quantity"] > 0 and not meets_partial_minimum(partial["quantity"], quantity):
        result["reason"] = (f"Only {partial['quantity']} of {quantity} could be ready by the deadline, below the "
                            f"{MIN_PARTIAL_FRACTION:.0%} minimum for a partial order. {plan['reason']}")
    elif partial["quantity"] > 0:
        result.update({
            "available": "partial",
            "available_quantity": partial["quantity"],
            "ready_date": partial["ready_date"],
            "reason": f"Only {partial['quantity']} of {quantity} can be ready by the deadline. {plan['reason']}",
        })
        _request_context["approved"][item_name] = partial["quantity"]
        _request_context["partial"][item_name] = quantity
    else:
        result["reason"] = plan["reason"]
    return json.dumps(result)


# Tools for quoting agent

@tool
def search_past_quotes(search_terms: list) -> str:
    """
    Search historical quotes for similar past requests, to keep pricing and explanations consistent.

    Args:
        search_terms: A list of keywords such as item names or event types, e.g. ["cardstock", "ceremony"].

    Returns:
        A JSON list of up to 5 matching past quotes with their totals and explanations.
    """
    return json.dumps(search_quote_history([str(term) for term in search_terms], limit=5), default=str)


@tool
def price_line_item(item_name: str, quantity: int) -> str:
    """
    Calculate the customer price of one line of a quote, including the bulk discount.
    Discount tiers: 100+ units 5%, 500+ units 10%, 1000+ units 15%.

    Args:
        item_name: The catalog item_name confirmed by check_availability (or the customer's description of it).
        quantity: The number of units being quoted.

    Returns:
        A JSON object with unit price, discount rate, discounted unit price and line total.
    """
    resolved = _resolve_requested_item(item_name)
    if resolved is None or _request_context["approved"].get(resolved) != quantity:
        return _not_approved_error(resolved or item_name, quantity, "quoted")
    return json.dumps(_price_line(resolved, quantity))


# Tools for ordering agent

@tool
def record_sale(item_name: str, quantity: int) -> str:
    """
    Record a confirmed sale of one line item at the quoted bulk-discount price, first ordering
    stock from the supplier if needed. Refuses if the item cannot be ready by the deadline.

    Args:
        item_name: The catalog item_name confirmed by check_availability (or the customer's description of it).
        quantity: The number of units sold.

    Returns:
        A confirmation with the transaction ID and ready date, or an error message.
    """
    resolved = _resolve_requested_item(item_name)
    if resolved is None:
        return _not_approved_error(item_name, quantity, "sold")
    with _db_write_lock:
        return _record_sale_locked(resolved, quantity)


def _record_sale_locked(item_name: str, quantity: int) -> str:
    sale_date = _request_date()
    if _request_context["approved"].get(item_name) != quantity:
        return _not_approved_error(item_name, quantity, "sold")
    plan = _plan_fulfillment(item_name, quantity)
    if not plan["available"]:
        return f"ERROR: cannot sell {quantity} x {item_name}. {plan['reason']}"
    if plan["reorder_quantity"] > 0:
        _ensure_in_inventory_table(item_name)
        create_transaction(item_name, "stock_orders", plan["reorder_quantity"], plan["cost"], sale_date)
    line_total = _price_line(item_name, quantity)["line_total"]
    transaction_id = create_transaction(item_name, "sales", quantity, line_total, sale_date)
    del _request_context["approved"][item_name]
    _request_context["sold"].append((item_name, quantity, line_total))
    return (f"Sale recorded (transaction {transaction_id}): {quantity} x {item_name} for ${line_total:.2f}, "
            f"ready {plan['ready_date']}.")


@tool
def financial_summary() -> str:
    """
    Get the company's financial position on the date of the current request: cash, inventory value,
    total assets and the top-selling products. For internal use only; never share these figures
    with the customer.

    Returns:
        A JSON object with cash_balance, inventory_value, total_assets and top_selling_products.
    """
    report = generate_financial_report(_request_date())
    return json.dumps({
        "cash_balance": round(report["cash_balance"], 2),
        "inventory_value": round(report["inventory_value"], 2),
        "total_assets": round(report["total_assets"], 2),
        # Skip the starter's opening-cash entry, which is recorded as a sale with no item
        "top_selling_products": [row for row in report["top_selling_products"] if row["item_name"]],
    }, default=str)


# Set up your agents and create an orchestration agent that will manage them.

inventory_agent = ToolCallingAgent(
    tools=[list_inventory, check_availability],
    model=model,
    name="inventory_agent",
    description=(
        "Matches each of the customer's item descriptions to a catalog item and checks whether it can be "
        "ready by the deadline, from stock or a supplier reorder. Give it the full list of requested items with quantities in sheets or "
        "units. It reports which items can be supplied by the customer's deadline."
    ),
    instructions=(
        "For each requested item, call check_availability exactly once with the customer's description "
        "copied verbatim (e.g. 'colorful cardstock', not a catalog name you chose) and the full quantity. "
        "The tool picks the catalog item itself. Never check alternatives, substitutes or partial quantities. "
        "You may call list_inventory once for context on what is in stock, but only check_availability "
        "decides availability, and stock levels must never appear in your answer. "
        "In your final answer, list every item as: customer description | catalog item_name from the tool "
        "(or 'not carried') | requested quantity | available (yes/partial/no) | available_quantity | "
        "ready date | reason if not fully available."
    ),
    max_steps=15,
    max_tool_threads=1,  # tools write to SQLite; run them one at a time
)

quoting_agent = ToolCallingAgent(
    tools=[search_past_quotes, price_line_item],
    model=model,
    name="quoting_agent",
    description=(
        "Prices a list of available items (exact catalog names and quantities) with bulk discounts, using "
        "past quotes for context. Returns line totals and a quote total."
    ),
    instructions=(
        "Call price_line_item for every item you are given, using the catalog item_name and quantity "
        "exactly as given; never invent prices. If it is rejected, retry with a confirmed item it lists. "
        "Optionally call search_past_quotes once for context on similar requests. "
        "Finish with each item's quantity, discounted unit price, discount rate and line total, "
        "plus the overall total."
    ),
    max_steps=12,
    max_tool_threads=1,  # tools write to SQLite; run them one at a time
)

sales_agent = ToolCallingAgent(
    tools=[record_sale, financial_summary],
    model=model,
    name="sales_agent",
    description=(
        "Finalizes an order by recording a sale for each quoted line item. Give it the exact catalog item "
        "names and quantities."
    ),
    instructions=(
        "Call record_sale once per line item with the exact item name and quantity; it charges the quoted price. "
        "If it is rejected, retry with a confirmed item it lists. "
        "After recording the sales, call financial_summary once to confirm the books updated. Its "
        "figures are internal: do not include them in your final answer. "
        "Finish with which sales succeeded and which failed."
    ),
    max_steps=12,
    max_tool_threads=1,  # tools write to SQLite; run them one at a time
)

orchestrator = ToolCallingAgent(
    tools=[],
    model=model,
    managed_agents=[inventory_agent, quoting_agent, sales_agent],
    name="orchestrator",
    instructions=(
        "You are the customer service front desk of Munder Difflin Paper Company. For each request:\n"
        "1. Extract every requested item with its quantity, exactly as written in the request.\n"
        "2. Send the full item list to inventory_agent, once, in the customer's own wording. It matches "
        "each line to at most one catalog item: never ask for similar or substitute items, and never split "
        "a quantity across products. If a line has no match or is unavailable, it is simply not supplied.\n"
        "3. Send only the available and partially available items to quoting_agent, using the exact "
        "catalog item_name values reported by inventory_agent and each item's available_quantity "
        "(for partial items this is less than requested).\n"
        "4. Send the quoted lines (exact item names and available quantities) to sales_agent. Always sell "
        "every available and partially available item, even if other items are unavailable; never ask "
        "the customer to confirm first.\n"
        "5. Write the final answer to the customer: the items sold, named by their catalog item_name, with quantities, the line totals and "
        "discounts from quoting_agent and their sum as the total, the delivery date, and which items you "
        "cannot supply. For partially supplied items, say how many of the requested quantity will be "
        "supplied and that the rest is unavailable by the deadline. Only list items whose sale sales_agent recorded. "
        "Be polite and concise. Never mention stock levels, restock costs, cash, funds, suppliers, "
        "internal agents or tool errors; for unavailable items just say they are unavailable by the "
        "deadline or not something we carry."
    ),
    max_steps=10,
    max_tool_threads=1,  # tools write to SQLite; run them one at a time
)


def _reply_problems(reply: str) -> List[str]:
    return reply_problems(reply, _request_context["sold"], _request_context["partial"])


def call_multi_agent_system(request: str, request_date: str) -> str:
    request = _convert_reams_to_sheets(request)
    _reset_request_context(request_date, _parse_deadline(request, request_date))
    try:
        response = str(orchestrator.run(request, reset=True))
        # Approvals are removed as items are sold, so any left over are available lines the
        # orchestrator skipped. Send it back once, in the same conversation, to sell them.
        unsold = _request_context["approved"]
        if unsold:
            lines = ", ".join(f"{qty} x {name}" for name, qty in unsold.items())
            print(f"UNSOLD APPROVED LINES: {lines}; asking the orchestrator to sell them")
            response = str(orchestrator.run(
                f"These lines were confirmed available but were not sold: {lines}. Send them to "
                f"quoting_agent and then sales_agent with exactly these item names and quantities. Then "
                f"write the complete final reply to the customer again, covering every item sold in this "
                f"request and every item that could not be supplied.",
                reset=False,
            ))
        # Check the reply against what was recorded, and ask for one rewrite if it does not match.
        for attempt in range(1, MAX_REPLY_REWRITES + 1):
            problems = _reply_problems(response)
            if not problems:
                break
            print(f"REPLY CHECK FAILED: {problems}; asking the orchestrator to rewrite the reply (attempt {attempt})")
            response = str(orchestrator.run(
                "Your reply to the customer has these problems: " + " ".join(problems) + " "
                + reply_requirements(_request_context["sold"], _request_context["partial"]) + " All sales are already recorded, so do not call any agents. "
                "Rewrite the complete final reply to the customer.",
                reset=False,
            ))
        else:
            remaining = _reply_problems(response)
            if remaining:
                print(f"REPLY CHECK STILL FAILING after {MAX_REPLY_REWRITES} rewrites: {remaining}")
        return response
    finally:
        _reset_request_context()


# Run your test scenarios by writing them here. Make sure to keep track of them.

def run_test_scenarios():
    
    print("Initializing Database...")
    init_database(db_engine)
    try:
        quote_requests_sample = pd.read_csv("quote_requests_sample.csv")
        quote_requests_sample["request_date"] = pd.to_datetime(
            quote_requests_sample["request_date"], format="%m/%d/%y", errors="coerce"
        )
        quote_requests_sample.dropna(subset=["request_date"], inplace=True)
        quote_requests_sample = quote_requests_sample.sort_values("request_date")
    except Exception as e:
        print(f"FATAL: Error loading test data: {e}")
        return

    # Get initial state
    initial_date = quote_requests_sample["request_date"].min().strftime("%Y-%m-%d")
    report = generate_financial_report(initial_date)
    current_cash = report["cash_balance"]
    current_inventory = report["inventory_value"]
    starting_cash, starting_inventory = current_cash, current_inventory

    ############
    ############
    ############
    # INITIALIZE YOUR MULTI AGENT SYSTEM HERE
    ############
    ############
    ############

    results = []
    for idx, row in quote_requests_sample.iterrows():
        request_date = row["request_date"].strftime("%Y-%m-%d")

        print(f"\n=== Request {idx+1} ===")
        print(f"Context: {row['job']} organizing {row['event']}")
        print(f"Request Date: {request_date}")
        print(f"Cash Balance: ${current_cash:.2f}")
        print(f"Inventory Value: ${current_inventory:.2f}")

        # Process request
        request_with_date = f"{row['request']} (Date of request: {request_date})"

        ############
        ############
        ############
        # USE YOUR MULTI AGENT SYSTEM TO HANDLE THE REQUEST
        ############
        ############
        ############

        try:
            response = call_multi_agent_system(request_with_date, request_date)
        except Exception as e:
            print(f"ERROR: agent system failed on request {idx+1}: {e}")
            response = "Sorry, we could not process your request right now. Please try again later."

        # Update state
        report = generate_financial_report(request_date)
        current_cash = report["cash_balance"]
        current_inventory = report["inventory_value"]

        print(f"Response: {response}")
        print(f"Updated Cash: ${current_cash:.2f}")
        print(f"Updated Inventory: ${current_inventory:.2f}")

        results.append(
            {
                "request_id": idx + 1,
                "request_date": request_date,
                "cash_balance": current_cash,
                "inventory_value": current_inventory,
                "response": response,
            }
        )

        time.sleep(1)

    # Final report
    final_date = quote_requests_sample["request_date"].max().strftime("%Y-%m-%d")
    final_report = generate_financial_report(final_date)
    print("\n===== FINAL FINANCIAL REPORT =====")
    print(f"Final Cash: ${final_report['cash_balance']:.2f}")
    print(f"Final Inventory: ${final_report['inventory_value']:.2f}")

    # Save results
    pd.DataFrame(results).to_csv("test_results.csv", index=False)

    # Check the saved results against properties every run must satisfy
    report_result_checks(check_results("test_results.csv", starting_cash, starting_inventory), "test_results.csv")
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
