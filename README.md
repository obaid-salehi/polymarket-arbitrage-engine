# Real-Time Polymarket Arbitrage Detection Engine

---

This project is a high-frequency arbitrage detection system designed for **Polymarket**, the world’s largest decentralized prediction market. The engine monitors the Central Limit Order Book (CLOB) in real-time via WebSockets to identify risk-free opportunities—specifically when the combined price of all outcomes in a binary market falls below $1.00$.

The system utilizes a custom **Paper Trading Engine** to simulate execution and track performance. In initial testing across high-volume "Yes/No" markets, the bot demonstrated the ability to capture sub-second price inefficiencies with a latency-sensitive verification loop.

---

## Project Pipeline & Methodology

The core challenge of this project was managing high-throughput data streams while ensuring that execution signals were verified against live order book depth to prevent "ghost" arbitrage.

### 1. Dynamic Market Discovery & Filtering
To ensure capital is only deployed in liquid environments, the system implements a rigorous filtering pipeline via `fetch_markets.py`.
* **Volume Thresholding:** Filters for markets with a `volumeNum` between 10,000 and 20,000 to focus on active yet potentially inefficient mid-cap markets.
* **Outcome Standardization:** Limits scope to binary `["Yes", "No"]` outcomes to simplify the arbitrage calculation and ensure high-speed processing.
* **Pagination Logic:** Implements an offset-based fetching system to bypass API rate limits while building a local map of active `conditionIds`.

### 2. Real-Time WebSocket Monitoring
The `monitor_markets.py` script establishes a persistent connection to the Polymarket CLOB.
* **Asset Mapping:** On startup, the system extracts `clobTokenIds` and maps them to their parent markets. It then issues a single `subscribe` command for all relevant assets.
* **Event Handling:** The engine listens specifically for `best_bid_ask` events. By focusing only on the top-of-book (Best Ask), the bot minimizes computational overhead.
* **Connection Resilience:** Includes a heartbeat "PING" thread and automatic exit/restart triggers if the socket receives a "market_resolved" event, ensuring the bot doesn't trade on settled markets.

### 3. Arbitrage Logic & Signal Detection
The `ArbitrageDetector` class acts as the brain of the operation, maintaining a local state of the latest prices for every tracked market.
* **Summation Trigger:** Whenever a price update occurs, the bot recalculates the sum of the Best Asks.
* **Profit Threshold:** A signal is only triggered if the total cost is less than $0.995. This 50-basis-point buffer accounts for potential slippage and execution delays.

### 4. Mock Execution & Performance Tracking
To validate the strategy without financial risk, `mock_trader.py` provides a realistic simulation environment.
* **Double-Verification Loop:** Upon receiving a signal, the trader performs a fresh REST API call to `clob.polymarket.com/book` to verify that the price is still available.
* **Latency Profiling:** The system measures the "Signal-to-Verify" latency in milliseconds (ms), providing critical data on whether the bot is fast enough for live deployment.
* **PnL Logging:** Tracks cumulative profit and loss, win/loss ratios, and per-trade yield based on a $1.00$ payout per contract.

---

## Results

Given the lack of arbitrage opportunities during live monitoring, the bot did not complete trades. However, during black-box testing, the bot was successfuly able to handle the detection and execution process multiple times resulting in a positive PnL and high win rate.

* **Execution Speed:** Average verification latency of **~150ms-300ms** (dependent on network conditions).
* **Profitability:** Successfully captured signals where the total market cost sat between **0.985 and 0.994**.
* **Reliability:** The Paper Trader successfully filtered out "stale" signals where the price moved between the WebSocket update and the REST verification.

---

## Tech Stack

* **Python**
* **Websocket-client:** For low-latency connection to the Polymarket CLOB.
* **Requests:** For Gamma API market discovery and REST-based price verification.
* **Threading:** To handle concurrent WebSocket listening and heartbeat pings.
* **JSON:** For parsing complex nested market data and token mapping.

---

## Future Improvements

* **Order Book Depth Analysis:** Instead of just checking the Best Ask, analyze the `size` available to determine the maximum capital that can be deployed per arbitrage.
* **Multi-Market Detection:** Expand the logic to handle multi-outcome markets where the sum of all "Yes" tokens should equal $1.00$.
* **Gas & Fee Integration:** Factor in Polygon network gas fees and potential exchange fees to calculate a true net-profit threshold.
* **C++ Implementation:** C++ is superior for high frequency trading and therefore would be the better language to implement the arbitrage engine with.
