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


import difflib
import json
from smolagents import OpenAIServerModel, ToolCallingAgent, tool

# Set up and load your env parameters and instantiate your model.
dotenv.load_dotenv()

model = OpenAIServerModel(
    model_id=os.getenv("OPENAI_MODEL_ID", "gpt-4o-mini"),
    api_base="https://openai.vocareum.com/v1",
    api_key=os.getenv("UDACITY_OPENAI_API_KEY"),
)

# Business rules shared by the tools
CATALOG = {item["item_name"]: item for item in paper_supplies}
DEFAULT_MIN_STOCK_LEVEL = 100
# (minimum quantity, discount rate), checked from largest tier down
BULK_DISCOUNT_TIERS = [(1000, 0.15), (500, 0.10), (100, 0.05), (0, 0.0)]


def _normalize_date(date_str: str) -> str:
    """Reduce any ISO date or datetime string to YYYY-MM-DD."""
    return str(date_str).split("T")[0].strip()


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


def _bulk_discount_rate(quantity: int) -> float:
    for min_quantity, rate in BULK_DISCOUNT_TIERS:
        if quantity >= min_quantity:
            return rate
    return 0.0


"""Set up tools for your agents to use, these should be methods that combine the database functions above
 and apply criteria to them to ensure that the flow of the system is correct."""


# Tools for inventory agent

@tool
def find_catalog_items(description: str) -> str:
    """
    Find the catalog items that best match a customer's description of a product.
    Always use this before any other tool so that exact catalog item names are used.

    Args:
        description: The customer's wording for the item, e.g. "A4 glossy paper" or "heavy cardstock".

    Returns:
        A JSON list of up to 5 candidate items with their exact item_name, category and unit_price,
        or a message saying nothing in the catalog matches.
    """
    query = description.lower()
    query_words = set(query.replace("-", " ").split())
    scored = []
    for name, item in CATALOG.items():
        name_lower = name.lower()
        name_words = set(name_lower.replace("-", " ").replace("(", " ").replace(")", " ").split())
        overlap = len(query_words & name_words) / max(len(name_words), 1)
        similarity = difflib.SequenceMatcher(None, query, name_lower).ratio()
        score = overlap + similarity
        if overlap > 0 or similarity >= 0.5:
            scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    if not scored:
        return f"No catalog item matches '{description}'. We do not sell this item."
    return json.dumps([item for _, item in scored[:5]])


@tool
def check_stock(item_name: str, as_of_date: str) -> str:
    """
    Check how many units of a catalog item are in stock on a given date.

    Args:
        item_name: The exact catalog item name, as returned by find_catalog_items.
        as_of_date: The date to check, in YYYY-MM-DD format.

    Returns:
        A JSON object with the item's current stock and minimum stock level.
    """
    if item_name not in CATALOG:
        return f"ERROR: '{item_name}' is not an exact catalog item name. Use find_catalog_items first."
    as_of_date = _normalize_date(as_of_date)
    return json.dumps({
        "item_name": item_name,
        "as_of_date": as_of_date,
        "current_stock": _current_stock(item_name, as_of_date),
        "min_stock_level": _min_stock_level(item_name),
    })


@tool
def restock_item(item_name: str, quantity_needed: int, order_date: str, deadline: str) -> str:
    """
    Make sure enough stock of an item will be available for a customer order, buying from the
    supplier if necessary. Orders enough to cover the shortfall plus the item's minimum stock level.
    Refuses if the supplier cannot deliver by the deadline or the company cannot afford the purchase.

    Args:
        item_name: The exact catalog item name, as returned by find_catalog_items.
        quantity_needed: The number of units the customer wants.
        order_date: The date of the customer request, in YYYY-MM-DD format.
        deadline: The date the customer needs the items by, in YYYY-MM-DD format.

    Returns:
        A message saying whether the item is available by the deadline, and when.
    """
    if item_name not in CATALOG:
        return f"ERROR: '{item_name}' is not an exact catalog item name. Use find_catalog_items first."
    order_date = _normalize_date(order_date)
    deadline = _normalize_date(deadline)

    stock = _current_stock(item_name, order_date)
    if stock >= quantity_needed:
        return json.dumps({
            "item_name": item_name,
            "available": True,
            "restocked_units": 0,
            "ready_date": order_date,
            "note": f"{stock} units already in stock.",
        })

    reorder_quantity = quantity_needed - stock + _min_stock_level(item_name)
    delivery_date = get_supplier_delivery_date(order_date, reorder_quantity)
    if delivery_date > deadline:
        return json.dumps({
            "item_name": item_name,
            "available": False,
            "reason": f"Only {stock} units in stock and the supplier cannot deliver until {delivery_date}, "
                      f"after the {deadline} deadline.",
        })

    cost = reorder_quantity * CATALOG[item_name]["unit_price"]
    cash = get_cash_balance(order_date)
    if cost > cash:
        return json.dumps({
            "item_name": item_name,
            "available": False,
            "reason": f"Restocking would cost ${cost:.2f} but only ${cash:.2f} cash is available.",
        })

    _ensure_in_inventory_table(item_name)
    create_transaction(item_name, "stock_orders", reorder_quantity, cost, order_date)
    return json.dumps({
        "item_name": item_name,
        "available": True,
        "restocked_units": reorder_quantity,
        "restock_cost": round(cost, 2),
        "ready_date": delivery_date,
    })


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
    Calculate the price of one line of a quote, including the bulk discount.
    Discount tiers: 100+ units 5%, 500+ units 10%, 1000+ units 15%.

    Args:
        item_name: The exact catalog item name, as returned by find_catalog_items.
        quantity: The number of units being quoted.

    Returns:
        A JSON object with unit price, discount rate, discounted unit price and line total.
    """
    if item_name not in CATALOG:
        return f"ERROR: '{item_name}' is not an exact catalog item name. Use find_catalog_items first."
    unit_price = CATALOG[item_name]["unit_price"]
    discount_rate = _bulk_discount_rate(quantity)
    discounted_unit_price = unit_price * (1 - discount_rate)
    return json.dumps({
        "item_name": item_name,
        "quantity": quantity,
        "unit_price": unit_price,
        "discount_rate": discount_rate,
        "discounted_unit_price": round(discounted_unit_price, 4),
        "line_total": round(discounted_unit_price * quantity, 2),
    })


# Tools for ordering agent

@tool
def record_sale(item_name: str, quantity: int, line_total: float, sale_date: str) -> str:
    """
    Record a confirmed sale of one line item. Refuses if there is not enough stock.

    Args:
        item_name: The exact catalog item name.
        quantity: The number of units sold.
        line_total: The total price charged for this line, from the quote.
        sale_date: The date of the customer request, in YYYY-MM-DD format.

    Returns:
        A confirmation with the transaction ID, or an error message.
    """
    if item_name not in CATALOG:
        return f"ERROR: '{item_name}' is not an exact catalog item name."
    sale_date = _normalize_date(sale_date)
    stock = _current_stock(item_name, sale_date)
    if stock < quantity:
        return f"ERROR: only {stock} units of {item_name} in stock; cannot sell {quantity}."
    transaction_id = create_transaction(item_name, "sales", quantity, line_total, sale_date)
    return f"Sale recorded (transaction {transaction_id}): {quantity} x {item_name} for ${line_total:.2f}."


@tool
def check_cash_balance(as_of_date: str) -> str:
    """
    Get the company's cash balance on a given date.

    Args:
        as_of_date: The date to check, in YYYY-MM-DD format.

    Returns:
        The cash balance in dollars.
    """
    return f"${get_cash_balance(_normalize_date(as_of_date)):.2f}"


# Set up your agents and create an orchestration agent that will manage them.

inventory_agent = ToolCallingAgent(
    tools=[find_catalog_items, check_stock, restock_item],
    model=model,
    name="inventory_agent",
    description=(
        "Maps the customer's item descriptions to exact catalog item names, checks stock, and restocks from "
        "the supplier when needed. Give it the full list of requested items with quantities, the request "
        "date and the delivery deadline. It reports which items can be supplied by the deadline."
    ),
    instructions=(
        "For each requested item: call find_catalog_items and pick the single best exact match. "
        "If nothing is a reasonable match (e.g. balloons, A3 paper), mark it as not sold. "
        "Convert reams to sheets (1 ream = 500 sheets). "
        "For each matched item call restock_item with the quantity, request date and deadline. "
        "Finish with a list of: requested description, exact catalog item_name, quantity, available "
        "(yes/no), ready date or reason."
    ),
    max_steps=15,
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
        "Call price_line_item for every item you are given; never invent prices. "
        "Optionally call search_past_quotes once for context on similar requests. "
        "Finish with each item's quantity, discounted unit price, discount rate and line total, "
        "plus the overall total."
    ),
    max_steps=12,
)

sales_agent = ToolCallingAgent(
    tools=[record_sale, check_cash_balance],
    model=model,
    name="sales_agent",
    description=(
        "Finalizes an order by recording a sale for each quoted line item. Give it the exact catalog item "
        "names, quantities, line totals and the request date."
    ),
    instructions=(
        "Call record_sale once per line item using the exact line totals you were given. "
        "Finish with which sales succeeded and which failed."
    ),
    max_steps=12,
)

orchestrator = ToolCallingAgent(
    tools=[],
    model=model,
    managed_agents=[inventory_agent, quoting_agent, sales_agent],
    name="orchestrator",
    instructions=(
        "You are the customer service front desk of Munder Difflin Paper Company. For each request:\n"
        "1. Extract every requested item with its quantity, the request date and the delivery deadline "
        "(YYYY-MM-DD). If no deadline is given, use 14 days after the request date.\n"
        "2. Send the full item list, request date and deadline to inventory_agent.\n"
        "3. Send only the available items (exact catalog names and quantities) to quoting_agent.\n"
        "4. Send the quoted lines and request date to sales_agent to record the sales.\n"
        "5. Write the final answer to the customer: the items you will supply with quantities, prices, "
        "discounts and total, the delivery date, and which items you cannot supply and why. "
        "Be polite and concise. Do not reveal internal details such as cash balance, supplier costs, "
        "stock levels or tool errors."
    ),
    max_steps=10,
)


def call_multi_agent_system(request: str) -> str:
    return str(orchestrator.run(request, reset=True))


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
            response = call_multi_agent_system(request_with_date)
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
    return results


if __name__ == "__main__":
    results = run_test_scenarios()
