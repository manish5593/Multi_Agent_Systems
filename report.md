# Munder Difflin Multi-Agent System: Project Report

## 1. Summary

This project builds a multi-agent system that handles free-text customer orders for the fictional Munder Difflin Paper Company. For each request, the system:

1. matches the customer's wording to catalog items,
2. checks whether each item can be ready by the deadline, from stock or a supplier reorder,
3. quotes prices with bulk discounts,
4. records the sales, and
5. replies to the customer.

The system uses four agents, under the limit of five, built with `smolagents` on `gpt-4o-mini`. A full run over the 20 sample requests produced at least one sale in 16 requests. None of the 33 sales was mispriced or sold below cost. Total assets rose from $50,000.00 to $51,007.60.

The main design lesson was this: **let the LLM decide what to do, and let Python do every calculation, match and database write.** Most bugs found during testing came from the LLM choosing dates, quantities, prices or catalog items. Each was fixed by moving that decision into deterministic code.

For the full tool reference and the reasoning behind each design decision, see [`design_notes.txt`](design_notes.txt).

## 2. Architecture

![Workflow diagram](workflow_diagram.png)

| Agent | Tools | Role |
|---|---|---|
| **Orchestrator** | delegates to the three agents below | Extracts the requested items, delegates in order, sells everything available, and writes the customer reply. |
| **Inventory agent** | `check_availability` | Passes each line of the customer's wording to the tool, which matches it to one catalog item and checks stock, supplier lead time and cash. Read-only. |
| **Quoting agent** | `price_line_item`, `search_past_quotes` | Prices approved items: the supplier cost plus a 25% markup, less 5%, 10% or 15% bulk discounts. |
| **Sales agent** | `record_sale`, `check_cash_balance` | Records each approved line. Places a supplier reorder first if needed. |

Python handles several things before and around the agents:

- **Before the agents run:** `call_multi_agent_system()` converts reams to sheets, sets the request date and parses the delivery deadline from the request text.
- **Approvals:** during the request it tracks which item and quantity `check_availability` approved for each line.
- **The guard:** only approved items can be quoted or sold, and each approval can be used only once.
- **Concurrency:** all tools run one at a time, and sale writes are locked.

## 3. Evaluation of test results

Results are in [`test_results.csv`](test_results.csv), from a full run of `quote_requests_sample.csv`.

### Headline results

| Metric | Result |
|---|---|
| Requests processed without error | 20 / 20 |
| Requests with at least one sale | 16 / 20 |
| Requested lines fulfilled (of lines checked) | 33 of 60 |
| Lines declined because the item is not carried | 11 (mostly A3/A5 paper; also balloons, cardboard, tickets) |
| Lines declined because the deadline couldn't be met | 16 |
| Sales priced exactly at cost × 1.25 less the bulk discount | 33 / 33 |
| Sales below cost | 0 |
| Stock bought without a matching sale | 0 |
| Items with negative stock | 0 |
| Replies revealing stock levels, costs, markup or cash | 0 |
| Replies asking the customer to confirm instead of selling | 0 |
| Database integrity check | passed |
| Revenue / restock spending | $14,838.10 / $13,262.60 |
| Cash / inventory / total assets | $46,635.20 / $4,372.40 / $51,007.60 (started at $50,000.00) |

### Per-request outcomes

| # | Date | Sold | Total | Not supplied |
|---|---|---|---|---|
| 1 | 04-01 | Glossy paper 200, Cardstock 100, Colored paper 100 | $77.19 | — |
| 2 | 04-03 | Poster paper 500, Party streamers 300 | $158.43 | balloons (not carried) |
| 3 | 04-04 | A4 paper 10,000; Standard copy paper 250,000 (500 reams) | $11,156.25 | A3 paper (not carried) |
| 4 | 04-05 | Cardstock 500, A4 paper 250 | $99.22 | — |
| 5 | 04-05 | Colored paper 500, Cardstock 300, Washi tape 200 | $157.19 | — |
| 6 | 04-06 | Construction paper 500, Standard copy paper 300, Cardstock 200 | $89.25 | — |
| 7 | 04-07 | Glossy paper 500, Large poster paper 300, Cardstock 200 | $504.37 | A3 matte paper (not carried) |
| 8 | 04-07 | Glossy paper 500, Matte paper 1,000, Recycled paper 3,000 | $558.75 | A5 colored paper (not carried) |
| 9 | 04-07 | — | — | A4 paper, envelopes (deadline Apr 10); A3 glossy (not carried) |
| 10 | 04-08 | Glossy paper 500, Cardstock 300 | $165.94 | — |
| 11 | 04-08 | Matte paper 300 | $64.12 | A3 glossy paper (not carried) |
| 12 | 04-08 | Cardstock 200, Standard copy paper 500, Paper napkins 100 | $60.50 | — |
| 13 | 04-08 | — | — | A4 paper, cardstock (deadline Apr 10) |
| 14 | 04-09 | Cardstock 500 | $84.38 | A4 paper, poster paper (deadline) |
| 15 | 04-12 | — | — | A4 paper (deadline); A3 colored paper, cardboard (not carried) |
| 16 | 04-13 | Large poster paper 100 | $118.75 | A4 paper, construction paper (deadline) |
| 17 | 04-14 | Paper plates 500 | $56.25 | A4 paper, napkins, cups (deadline); A3 colored (not carried) |
| 18 | 04-14 | — | — | cardstock, copy paper, colored paper (deadline) |
| 19 | 04-15 | Cardstock 1,000 | $159.38 | A4 glossy paper (deadline); A3 matte (not carried) |
| 20 | 04-17 | Flyers 5,000, Poster paper 2,000 | $1,328.13 | tickets (not carried) |

### Strengths

- **Prices and the books are correct by construction.** Prices come from one function shared by quoting and sales. Dates come from Python. Stock is bought only inside `record_sale`, for items actually sold. Every sale matched the expected price, and no stock order lacks a matching sale.
- **Deadlines are respected.** Every line declined for timing was declined because the supplier's lead time (up to 7 days for orders over 1,000 units) ends after the customer's deadline. Request 13, with an April 10 deadline, shows this clearly.
- **Catalog matching is consistent.** Everyday wording maps to the right item, for example "colorful cardstock" to Cardstock, "colorful construction paper" to Construction paper, and "poster boards (24" x 36")" to Large poster paper. Paper sizes the catalog doesn't stock, such as A3 and A5, are declined, not swapped for A4.
- **Large orders work.** Request 3's 500 reams were converted to 250,000 sheets, restocked in time, and sold at a profit: $10,625.00 in revenue against a $10,004.00 restock cost.
- **Replies are customer-safe.** They list items, prices, discounts and delivery dates, and never mention stock levels, costs, the markup or cash.

### Weaknesses

- **Many lines can't be filled by the deadline (16 of 60).** Supplier lead time is fixed by `get_supplier_delivery_date`, and only about 40% of catalog items start in stock. Later requests with April 15 deadlines leave too little time for any order over 1,000 units.
- **Matching is a heuristic.** It uses word overlap, a main-noun bonus and a few aliases, tuned on the sample wording. Brand names or unusual wording would need new aliases, and attributes like "recycled" or "white" are ignored.
- **No partial fulfillment.** If 10,000 sheets can't arrive by the deadline, the whole line is declined, even if most of it is in stock.
- **Some behavior still relies on the LLM following instructions,** such as copying the customer's wording verbatim and always selling available items. The tool guards prevent wrong sales, but they can't force a sale the agent skips.

## 4. What testing changed

The system went through about a dozen test runs. Each fix below came from a specific failure:

| Failure observed | Fix |
|---|---|
| LLM invented dates (e.g. 2023-11-24), causing false "insufficient funds" refusals and negative stock | Request date and deadline set in Python; tools take no dates |
| Sales recorded at undiscounted prices | One pricing function for quotes and sales |
| Checking availability bought stock for items never sold | Read-only `check_availability`; buying only in `record_sale` |
| Orchestrator sold 10 substitute products (~$36,000) for one order | Sales limited to items approved for that request |
| 500 reams quoted as 500 sheets | Reams converted to sheets in Python |
| Parallel tool calls corrupted the SQLite database | One tool call at a time, and a lock around sale writes |
| Discounted bulk sales lost money | 25% markup over supplier cost |
| Agents picked different catalog items for the same line | Matching done once in Python; quotes and sales resolve to the approved item |
| "250,000 sheets of cardboard" matched "250 gsm cardstock" via the quantity's digits | Leading quantities stripped before matching (spec numbers like "250 gsm" kept) |

## 5. Suggested improvements

1. **Partial fulfillment.** Offer what is in stock now, and backorder the rest with its later delivery date.
2. **Smarter matching.** Use embeddings, or an LLM ranking step limited to the catalog, to handle unfamiliar wording and attributes like "recycled".
3. **Better restocking.** Restock popular items ahead of demand instead of only when an order needs them, so more April 15 deadlines can be met.
4. **Structured handoffs.** Have agents pass JSON item lists, not free text, to remove the remaining LLM-dependent steps.

## 6. How to run

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "UDACITY_OPENAI_API_KEY=<your key>" > .env
python project_starter.py
```

The run takes about 15–25 minutes. It writes `test_results.csv` and prints the final financial report.
