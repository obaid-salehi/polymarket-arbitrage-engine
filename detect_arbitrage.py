from mock_trader import PaperTrader
import json

class OrderBook:
    def __init__(self):
        self.bids = {}  # price (float) -> size (float)
        self.asks = {}  # price (float) -> size (float)

    def update_from_snapshot(self, bids_data, asks_data):
        self.bids = {float(b["price"]): float(b["size"]) for b in bids_data if b.get("price") and b.get("size")}
        self.asks = {float(a["price"]): float(a["size"]) for a in asks_data if a.get("price") and a.get("size")}

    def update_price_level(self, side, price, size):
        target = self.bids if side == "BUY" else self.asks
        if size == 0.0:
            target.pop(price, None)
        else:
            target[price] = size

    def get_sorted_asks(self):
        return sorted(self.asks.items(), key=lambda x: x[0])


def calculate_optimal_arb(asks_A, asks_B, capital):
    idx_A = 0
    idx_B = 0
    total_volume = 0.0
    total_cost = 0.0
    rem_capital = capital
    
    execution_A = []  # list of (price, quantity)
    execution_B = []  # list of (price, quantity)
    
    if not asks_A or not asks_B:
        return 0.0, 0.0, 0.0, [], []
        
    rem_A = asks_A[0][1]
    rem_B = asks_B[0][1]
    p_A = asks_A[0][0]
    p_B = asks_B[0][0]
    
    while idx_A < len(asks_A) and idx_B < len(asks_B):
        marginal_cost = p_A + p_B
        if marginal_cost >= 1.00:
            break
            
        dq = min(rem_A, rem_B)
        if dq <= 0:
            break
            
        max_q_capital = rem_capital / marginal_cost
        step_q = min(dq, max_q_capital)
        if step_q <= 1e-8:
            break
            
        total_volume += step_q
        step_cost = step_q * marginal_cost
        total_cost += step_cost
        rem_capital -= step_cost
        
        execution_A.append((p_A, step_q))
        execution_B.append((p_B, step_q))
        
        rem_A -= step_q
        rem_B -= step_q
        
        if rem_A <= 1e-8:
            idx_A += 1
            if idx_A < len(asks_A):
                p_A = asks_A[idx_A][0]
                rem_A = asks_A[idx_A][1]
        if rem_B <= 1e-8:
            idx_B += 1
            if idx_B < len(asks_B):
                p_B = asks_B[idx_B][0]
                rem_B = asks_B[idx_B][1]
                
        if step_q < dq:
            break
            
    expected_profit = total_volume - total_cost
    return total_volume, total_cost, expected_profit, execution_A, execution_B


def aggregate_execution(execution_list):
    agg = {}
    for price, qty in execution_list:
        agg[price] = agg.get(price, 0.0) + qty
    return sorted(agg.items())


class ArbitrageDetector:
    def __init__(self):
        self.market_map = {}
        self.market_to_assets = {}
        self.orderbooks = {}
        self.trader = PaperTrader(1000) 
    
    def extract_token_ids(self, active_markets):
        active_token_ids = []
        for market in active_markets:
            market_id = market.get("conditionId", "")
            tokens_json = market.get("clobTokenIds", "[]")
            try:
                token_ids = json.loads(tokens_json)
            except:
                continue
            active_token_ids.extend(token_ids)
            self.market_to_assets[market_id] = token_ids
            for id in token_ids:
                self.market_map[id] = market_id
        return active_token_ids

    def process_ws_message(self, message):
        event_type = message.get("event_type")
        if event_type == "book":
            asset_id = message.get("asset_id")
            if not asset_id:
                return
            if asset_id not in self.orderbooks:
                self.orderbooks[asset_id] = OrderBook()
            self.orderbooks[asset_id].update_from_snapshot(
                message.get("bids", []),
                message.get("asks", [])
            )
            market_id = self.market_map.get(asset_id)
            if market_id:
                self.check_arb_for_market(market_id)
                
        elif event_type == "price_change":
            price_changes = message.get("price_changes", [])
            updated_markets = set()
            for pc in price_changes:
                asset_id = pc.get("asset_id")
                if not asset_id:
                    continue
                if asset_id not in self.orderbooks:
                    self.orderbooks[asset_id] = OrderBook()
                
                side = pc.get("side")
                try:
                    price = float(pc.get("price", 0.0))
                    size = float(pc.get("size", 0.0))
                except ValueError:
                    continue
                self.orderbooks[asset_id].update_price_level(side, price, size)
                
                market_id = self.market_map.get(asset_id)
                if market_id:
                    updated_markets.add(market_id)
                    
            for market_id in updated_markets:
                self.check_arb_for_market(market_id)

    def check_arb_for_market(self, market_id):
        assets = self.market_to_assets.get(market_id, [])
        if len(assets) != 2:
            return
            
        asset_A, asset_B = assets[0], assets[1]
        if asset_A not in self.orderbooks or asset_B not in self.orderbooks:
            return
            
        asks_A = self.orderbooks[asset_A].get_sorted_asks()
        asks_B = self.orderbooks[asset_B].get_sorted_asks()
        
        if not asks_A or not asks_B:
            return
            
        capital = self.trader.balance
        volume, cost, profit, exec_A, exec_B = calculate_optimal_arb(asks_A, asks_B, capital)
        
        if profit > 0.01 and volume > 0.0:  
            agg_exec_A = aggregate_execution(exec_A)
            agg_exec_B = aggregate_execution(exec_B)
            
            print(f"\n[ARB DETECTED] Market: {market_id}")
            print(f"  Deployable Capital: ${capital:.2f}")
            print(f"  Optimal Volume: {volume:.4f} shares")
            print(f"  Total Cost: ${cost:.4f}")
            print(f"  Expected Profit: ${profit:.4f} ({(profit/cost)*100:.2f}% return)")
            
            self.trader.execute_arb(market_id, volume, cost, profit, agg_exec_A, agg_exec_B)
