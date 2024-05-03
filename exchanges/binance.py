import logging
from typing import Dict, List, Union

import requests

from utils import Candle

logger = logging.getLogger()


class BinanceClient:
    def __init__(self, futures=False):

        self.futures = futures
        if self.futures:
            self._base_url = "https://fapi.binance.com"
        else:
            self._base_url = "https://api.binance.com"
        self.symbols = self._get_symbols()

    def _make_request(self, endpoint: str, query_paramenter: Dict):
        try:
            response = requests.get(self._base_url + endpoint, params=query_paramenter)
        except Exception as e:
            logger.error("Error while making request to %s: %s", endpoint, str(e))
            return None
        if response.status_code == 200:
            return response.json()
        else:
            logger.error("Error while making request to %s: %s (status code = %d)",
                         endpoint, response.json(), response.status_code)

    def _get_symbols(self) -> List[str]:
        params = dict()
        endpoint = "/fapi/v1/exchangeInfo" if self.futures else "/api/v3/exchangeInfo"
        data = self._make_request(endpoint, params)
        symbols = [x["symbol"] for x in data["symbols"]]

        return symbols

    def get_historical_data(self, symbol: str, start_time=None,
                            end_time=None, interval="1m") -> Union[None, List[Candle]]:
        params = dict()

        params["symbol"] = symbol
        params["interval"] = interval
        if start_time is not None:
            params["startTime"] = start_time
        if end_time is not None:
            params["endTime"] = end_time
        params["limit"] = 1500

        endpoint = "/fapi/v1/klines" if self.futures else "/api/v3/klines"
        raw_candles = self._make_request(endpoint, params)
        candles = []
        if raw_candles is not None:
            for c in raw_candles:
                candles.append(Candle(float(c[0]), float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])))
            return candles
        else:
            return None

    def place_future_order(self, symbol: str, long_short: int, limit_price: float,
                           amount_usd: float, stop_loss: float, take_profit: float):
        endpoint = "/sapi/v1/margin/order"
        params = dict()
        params["symbol"] = symbol
        params["side"] = "LONG" if long_short == 1 else "SHORT"

    def time(self):
        endpoint = "/api/v3/time"
        return self._make_request(endpoint, dict())["serverTime"]

    # get current price for symbol
    def get_current_price(self, symbol: str):
        endpoint = "/api/v3/ticker/price"
        params = dict()
        params["symbol"] = symbol
        return float(self._make_request(endpoint, params)["price"])