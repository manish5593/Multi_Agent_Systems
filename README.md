# Munder Difflin: Multi-Agent Order Processing

A multi-agent system that handles free-text customer orders for a fictional paper company. It matches the
customer's wording to catalog items, checks what can be ready by their deadline, quotes prices with bulk
discounts, records the sales, and writes the reply. It runs four agents built with
[`smolagents`](https://github.com/huggingface/smolagents) on `gpt-4o-mini`, backed by a SQLite database of stock,
supplier orders and transactions.

Built for the multi-agent systems project in Udacity's Agentic AI program, where the system could use at most
five agents.

**Results** from a full run over the 20 sample requests:

| Metric | Result |
|---|---|
| Requests processed without error | 20 / 20 |
| Requests with at least one sale | 19 / 20 |
| Sales priced correctly (cost × 1.25, less the bulk discount) | 39 / 39 |
| Sales below cost | 0 |
| Replies revealing stock levels, costs, markup or cash | 0 |
| Total assets | $50,000.00 → $51,045.98 |

The full breakdown, per request, is in [`report.md`](report.md).

## How it works

![Workflow diagram](workflow_diagram.png)

| Agent | Tools | Role |
|---|---|---|
| Orchestrator | the three agents below | Pulls the requested items out of the message, delegates to the agents in order, and writes the reply |
| Inventory agent | `check_availability`, `list_inventory` | Matches each line to one catalog item and checks stock, supplier lead time and cash against the deadline |
| Quoting agent | `price_line_item`, `search_past_quotes` | Prices approved items: supplier cost plus 25%, less 5%, 10% or 15% bulk discounts |
| Sales agent | `record_sale`, `financial_summary` | Records each approved line, ordering from the supplier first if needed |

The main design decision: **the agents decide what to do, and Python does every calculation, match and database
write.** Almost every bug found in testing came from the model choosing a date, quantity, price or catalog
item. Each was fixed by moving that choice into code. So in practice:

- **Dates:** dates and deadlines are parsed in Python, and the tools don't accept dates at all.
- **Prices:** quoting and sales share one pricing function.
- **Approvals:** only items that `check_availability` approved for this request can be sold, and each approval
  can be used once.
- **Reply checks:** Python checks the final reply against the recorded sales (the total, partial quantities, and
  no internal details) and asks for a rewrite if it's wrong.

The deterministic logic lives in small modules with no database access, so it can be tested on its own:
- `matching.py` and `catalog_ranking.py`: catalog matching, with rules first and then an embedding shortlist;
- `pricing.py`;
- `fulfillment.py`: full and partial orders;
- `reply_validation.py`.

## What testing changed

The system went through about a dozen full test runs. A few of the failures and fixes:

| What went wrong | Fix |
|---|---|
| The model invented dates such as 2023-11-24, causing false "insufficient funds" refusals and negative stock | Dates set in Python; tools take no dates |
| The orchestrator sold 10 substitute products, about $36,000, for one order | Sales limited to items approved for that request |
| "250,000 sheets of cardboard" matched "250 gsm cardstock" through the quantity's digits | Quantities stripped before matching |
| 500 reams quoted as 500 sheets | Reams converted to sheets in Python |
| Parallel tool calls corrupted the SQLite database | One tool call at a time, and a lock on sale writes |
| Discounted bulk sales lost money | 25% markup over supplier cost |
| "post-it notes" and "tablecloths" matched nothing, and "paper clips" matched Paper cups | Embedding shortlist after the rules. On 88 labeled descriptions it now gets 25 of 31 paraphrases (the lexical matcher got 19) and rejects all 16 items the company doesn't sell. |

The full list, with the reasoning behind each decision, is in [`report.md`](report.md) and
[`design_notes.txt`](design_notes.txt).

## Running it

Needs Python 3.11 and an OpenAI-compatible API key. The project was built against the Vocareum proxy at
`https://openai.vocareum.com/v1`.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "UDACITY_OPENAI_API_KEY=<your key>" > .env
python project_starter.py
```

Run it from the project folder. A full run takes about 15–25 minutes. It processes `quote_requests_sample.csv`,
writes `test_results.csv`, prints the final financial report, and then checks the results automatically.

## Tests

These run offline, with no API key:

```bash
python -m unittest test_validate_results test_catalog_ranking   # 17 tests
python validate_results.py                                       # checks test_results.csv
```

`python evaluate_matching.py` measures matching accuracy on the labeled descriptions. It calls the embeddings
API, so it needs the key in `.env`.

`validate_results.py` checks properties every run must satisfy, rather than one run's exact wording:
- no failed requests;
- no internal details in any reply;
- replies consistent with the recorded sales;
- cash and inventory never negative;
- total assets never falling between requests.

## Known limitations

- **Partial orders:** 12 of 60 lines were only partly filled, mostly because of fixed supplier lead times and
  low starting stock.
- **First drafts still fail:** 5 of the 20 first-draft replies failed the reply check and had to be rewritten.
  The checks catch these, but cost extra LLM calls.
- **Matching gaps:** some wording still matches the wrong item ("card stock" as two words) or nothing at all
  ("leaflets").
- **Agent compliance:** the guards prevent wrong sales, but they can't force a sale the agent skips.

## Files

| File | Contents |
|---|---|
| `project_starter.py` | Database helpers, tools, agents and the test loop |
| `matching.py`, `catalog_ranking.py`, `pricing.py`, `fulfillment.py`, `reply_validation.py` | Deterministic logic |
| `validate_results.py`, `test_*.py`, `evaluate_matching.py` | Result checks, unit tests and matching evaluation |
| `quote_requests_sample.csv`, `quotes.csv`, `quote_requests.csv` | Sample requests and historical quotes |
| `test_results.csv` | Results of the latest full run |
| `report.md`, `design_notes.txt`, `workflow_diagram.png` | Report, design notes and diagram |
