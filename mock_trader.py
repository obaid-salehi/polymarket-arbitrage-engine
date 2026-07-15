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

    def execute_arb(self, market_id, volume, cost, profit, exec_A, exec_B):
        self.balance += profit
        self.total_pnl += profit
        
        print(f"\n{"="*24} EXECUTION REPORT {"="*24}")
        print(f"Market: {market_id}")
        print(f"Volume Executed: {volume:.4f} shares")
        print(f"Total Cost: ${cost:.4f}")
        print(f"Guaranteed Payout: ${volume:.4f}")
        print(f"Net Profit: ${profit:.4f}")
        print(f"Fills for Asset A:")
        for price, qty in exec_A:
            print(f"  - Price: ${price:.4f} | Qty: {qty:.4f}")
        print(f"Fills for Asset B:")
        for price, qty in exec_B:
            print(f"  - Price: ${price:.4f} | Qty: {qty:.4f}")
            
        if profit > 0:
            self.wins += 1    
        else:
            self.losses += 1
            
        print(f"New Balance: ${self.balance:.2f} | Total PnL: ${self.total_pnl:.4f}")
        print(f"Wins: {self.wins} | Losses: {self.losses}")
        print(f"{"="*66}\n")
