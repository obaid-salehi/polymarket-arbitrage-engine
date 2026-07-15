# Real-Time Polymarket Arbitrage Detection Engine

---

This project is a high-frequency arbitrage detection system designed for **Polymarket**, the world’s largest decentralized prediction market. The engine monitors the Central Limit Order Book (CLOB) in real-time via WebSockets to identify risk-free opportunities—specifically when the combined price of all outcomes in a binary market falls below $1.00$.

The system utilizes a custom **Paper Trading Engine** to simulate execution and track performance. The bot tracks the complete L2 orderbook depth and dynamically calculates the optimal execution size to maximize guaranteed profit under capital constraints.

---

## Project Pipeline & Methodology

The core challenge of this project was managing high-throughput data streams while ensuring that execution signals were verified against live order book depth and sized correctly based on available liquidity and capital.

### 1. Dynamic Market Discovery & Filtering
To ensure capital is only deployed in liquid environments, the system implements a rigorous filtering pipeline via `fetch_markets.py`.
* **Volume Thresholding:** Filters for markets with a `volumeNum` between 10,000 and 20,000 to focus on active yet potentially inefficient mid-cap markets.
* **Outcome Standardization:** Limits scope to binary `["Yes", "No"]` outcomes to simplify the arbitrage calculation and ensure high-speed processing.
* **Pagination Logic:** Implements an offset-based fetching system to bypass API rate limits while building a local map of active `conditionIds`.

### 2. Real-Time WebSocket Monitoring
The `monitor_markets.py` script establishes a persistent connection to the Polymarket CLOB.
* **Asset Mapping:** On startup, the system extracts `clobTokenIds` and maps them to their parent markets. It then issues a subscription command for all relevant assets.
* **Event Handling:** The engine subscribes to the market feed with custom features enabled to listen to `book` snapshots and `price_change` delta events. This allows it to maintain a real-time local copy of the full L2 orderbook for every tracked asset.
* **Connection Resilience:** Includes a heartbeat "PING" thread and automatic exit/restart triggers if the socket receives a "market_resolved" event, ensuring the bot doesn't trade on settled markets.

### 3. Arbitrage Logic & Signal Detection
The `ArbitrageDetector` class acts as the brain of the operation, maintaining a local state of the bids and asks for every tracked asset.
* **Order Book Depth Analysis:** Instead of just checking the Best Ask, the detector processes the full ask depth (prices and sizes) of both YES and NO order books.
* **Profit Optimization:** Calculates the optimal capital-constrained volume to execute by walking up the order books. The engine stops buying when the marginal cost of YES + NO is >= $1.00 (i.e. zero or negative marginal profit) or when the trader's deployable capital limit is reached.

### 4. Mock Execution & Performance Tracking
To validate the strategy without financial risk, `mock_trader.py` provides a realistic simulation environment.
* **Direct Local Execution:** Since the L2 orderbook state is tracked in real-time, the double-verification loop (making REST API requests) has been removed to minimize execution latency.
* **Capital Auto-Sizing:** Executions are sized automatically against the trader's live deployable capital (`self.balance`), simulating immediate settlement and updating the balance with guaranteed profits.
* **PnL Logging:** Tracks cumulative profit and loss, win/loss ratios, and per-trade yield based on the exact filled prices across the order book levels.

---

## Results

During testing, the bot successfully handled the detection, volume optimization, and execution process multiple times, resulting in a positive PnL and high win rate.

* **Zero REST Overhead:** Eliminates the REST-based verification latency entirely, allowing immediate local execution of detected signals.
* **Optimized Volume:** Instead of simple binary triggers, the bot executes trades with optimal volume, capturing multi-level liquidity and maximizing net profit per signal.
* **Capital Tracking:** Keeps a dynamic record of deployable capital, compounding profits as trades resolve.

---

## Tech Stack

* **Python**
* **Websocket-client:** For low-latency connection to the Polymarket CLOB.
* **Requests:** For Gamma API market discovery.
* **Threading:** To handle concurrent WebSocket listening and heartbeat pings.
* **JSON:** For parsing complex nested market data and token mapping.

---

## Future Improvements

* **Multi-Market Detection:** Expand the logic to handle multi-outcome markets where the sum of all "Yes" tokens should equal $1.00$.
* **Gas & Fee Integration:** Factor in Polygon network gas fees and potential exchange fees to calculate a true net-profit threshold.
* **C++ Implementation:** C++ is superior for high frequency trading and therefore would be the better language to implement the arbitrage engine with.
