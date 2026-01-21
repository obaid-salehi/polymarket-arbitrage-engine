import requests
import time

class PaperTrader:
    def __init__(self, initial_balance):
        self.balance = initial_balance
        self.total_pnl = 0
        self.wins = 0
        self.losses = 0

    def get_live_price(self, token_id):
        try:
            url = f"https://clob.polymarket.com/book?token_id={token_id}"
            response = requests.get(url)
            if response.status_code == 200:   
                data = response.json()
                asks = data.get("asks", [])
                if asks:
                    return float(asks[0]["price"])
        except:
            print("Error fetching price. ")
        return None

    def execute_arb(self, market_id, assets):
        print(f"Verifying Arb for Market {market_id} via API. ")
        start_time = time.time()
        verified_prices = {}
        for asset_id in assets.keys():
            live_price = self.get_live_price(asset_id)
            if live_price is None:
                print(f"Failed to verify price for {asset_id}")
                return
            verified_prices[asset_id] = live_price  
        total_cost = sum(verified_prices.values())
        pnl = 1.00 - total_cost
        self.total_pnl += pnl
        latency = (time.time() - start_time) * 1000
        print(f"Success Arb Executed in {latency}ms")
        if pnl > 0:
            self.wins += 1    
        else:
            self.losses += 1
        print(f"Arb PnL: {pnl:.4f} | Total PnL: {self.total_pnl:.4f}")
        print(f"Wins: {self.wins} | Losses: {self.losses}")