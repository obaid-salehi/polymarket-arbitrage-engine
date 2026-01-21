from mock_trader import PaperTrader
import json

class ArbitrageDetector:

    def __init__(self):
        self.market_map = {}
        self.prices = {}
        self.trader = PaperTrader(1000) # Initialize Trader
    
    def extract_token_ids(self,active_markets):
        active_token_ids = []
        for market in active_markets:
            market_id = market.get("conditionId", "")
            tokens_json = market.get("clobTokenIds", "[]")
            token_ids = json.loads(tokens_json)
            active_token_ids.extend(token_ids)
            for id in token_ids:
                self.market_map[id] = market_id
        return active_token_ids

    def check_arb(self, item):
        asset_id = item.get("asset_id")
        raw_price = item.get("best_ask")
        if not raw_price:
            return
        price = float(raw_price)
        market_id = item.get("market")
        if not market_id and asset_id:
             market_id = self.market_map.get(asset_id)
        if not market_id or not asset_id:
            return
        if market_id not in self.prices:
            self.prices[market_id] = {}
        self.prices[market_id][asset_id] = price
        if len(self.prices[market_id]) == 2:
            total = sum(self.prices[market_id].values())
            if total <= 0.995:
                print(f"ARB SIGNAL | Sum: {total:.4f} | Market: {market_id}")
                self.trader.execute_arb(market_id, self.prices[market_id])
        