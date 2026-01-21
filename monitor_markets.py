from websocket import WebSocketApp
import json
import time
import threading
from fetch_markets import get_markets_data
import ssl
from detect_arbitrage import ArbitrageDetector

MARKET_CHANNEL = "market"
USER_CHANNEL = "user"

class WebSocketOrderBook:
    def __init__(self, channel_type, url, data, auth, detector, verbose):
        self.channel_type = channel_type
        self.arb_detector = detector
        self.url = url
        self.data = data
        self.auth = auth
        self.verbose = verbose
        furl = url + "/ws/" + channel_type
        self.ws = WebSocketApp(
            furl,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if isinstance(data, dict):
                event_type = data.get("event_type","")
                if event_type == "best_bid_ask":
                    self.arb_detector.check_arb(data)
                elif data.get("winning_outcome","") != "":
                    print("Restarting Connection. ")
                    exit(0)
            elif isinstance(data, list):
                for item in data:
                    event_type = item.get("event_type","")
                    if event_type == "best_bid_ask":
                        self.arb_detector.check_arb(item)
                    elif item.get("winning_outcome","") != "":
                        print("Restarting Connection. ")
                        exit(0)
        except json.JSONDecodeError:
            pass

    def on_error(self, ws, error):
        print("Error: ", error)
        # exit(1)

    def on_close(self, ws):
        print("closing")
        exit(0)

    def on_open(self, ws):
        if self.channel_type == MARKET_CHANNEL:
            ws.send(json.dumps({"assets_ids": self.data, "type": MARKET_CHANNEL}))
        elif self.channel_type == USER_CHANNEL and self.auth:
            ws.send(json.dumps({"markets": self.data, "type": USER_CHANNEL, "auth": self.auth}))
        else:
            exit(1)

        thr = threading.Thread(target=self.ping, args=(ws,))
        thr.daemon = True
        thr.start()

    def subscribe_to_tokens_ids(self, ws, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "subscribe"}))

    def unsubscribe_to_tokens_ids(self, ws, assets_ids):
        if self.channel_type == MARKET_CHANNEL:
            self.ws.send(json.dumps({"assets_ids": assets_ids, "operation": "unsubscribe"}))

    def ping(self, ws):
        while True:
            ws.send("PING")
            time.sleep(10)

    def run(self):
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

def run_websocket():
    url = "wss://ws-subscriptions-clob.polymarket.com"
    api_key = ""
    api_secret = ""
    api_passphrase = ""
    active_markets = get_markets_data()
    arb_detector = ArbitrageDetector()
    active_token_ids = arb_detector.extract_token_ids(active_markets)
    auth = {"apiKey": api_key, "secret": api_secret, "passphrase": api_passphrase}
    market_connection = WebSocketOrderBook(MARKET_CHANNEL, url, active_token_ids, auth, arb_detector, True)
    print("Websocket Connection Complete. ")
    while True:
        market_connection.run()

if __name__ == "__main__":
    run_websocket()

