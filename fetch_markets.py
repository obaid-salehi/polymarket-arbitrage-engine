import requests
import datetime as dt
import json

def get_tags_data():
    tags_request = requests.get("https://gamma-api.polymarket.com/tags",params = {"limit": 1000000})
    tags_data = tags_request.json()
    return tags_data

def filter_markets(market):
    min_volume = 10000
    max_volume = 20000
    market_vol = market.get("volumeNum",0)
    if market_vol < min_volume or market_vol > max_volume:
        return True
    outcomes = market.get("outcomes", "[]")
    try:
        outcomes_list = json.loads(outcomes)
        if outcomes_list != ["Yes", "No"]: 
            return True
    except:
        return True
    return False

def get_markets_data():
    relevant_markets = []
    offset = 0
    limit = 100
    flag = True
    while flag:
        params = {
            "limit": limit,
            "offset": offset,
            "active": "true",
            "closed": "false",
            "order": "volumeNum",
            "ascending": "false"
        }
        markets_request = requests.get("https://gamma-api.polymarket.com/markets", params=params)
        markets_data = markets_request.json()
        num_r_markets = 500
        for market in markets_data:
            if len(relevant_markets) >= num_r_markets:
                flag = False
                break
            filtered = filter_markets(market)
            if not filtered:
                relevant_markets.append(market)
        print(f"{len(relevant_markets)} total relevant markets found.")
        offset += limit #pagination to prevent reaching rate limit
    return relevant_markets

if __name__ == "__main__":
    markets = get_markets_data()
    print(f"Fetched {len(markets)} active markets.")
    for market in markets:
        print(market)
