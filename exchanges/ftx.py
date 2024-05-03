import logging
from collections import namedtuple
from typing import Dict, List

import requests

logger = logging.getLogger()


class FTXClient:
    def __init__(self):

        self._base_url = "https://ftx.com/api"
        self.symbols = self._get_symbols()

    def _make_request(self, endpoint: str, query_paramenter: Dict):
        try:
            response = requests.get(self._base_url + endpoint, params=query_paramenter)
        except Exception as e:
            logger.error("Error while making request to %s: %s", endpoint, str(e))
            return None
        if response.status_code == 200:
            json_response = response.json()
            if json_response["success"]:
                return json_response["results"]
        else:
            logger.error("Error while making request to %s: %s (status code = %d)",
                         endpoint, response.json(), response.status_code)

    def _get_symbols(self) -> List[str]:
        params = dict()
        endpoint = "/market"
        data = self._make_request(endpoint, params)
        symbols = [x["name"] for x in data]
        print(symbols)

        return symbols

    def get_historical_data(self, symbol: str, start_time=None, end_time=None):
        params = dict()

        params["symbol"] = symbol
        params["interval"] = "1m"
        params["limit"] = 1500

        endpoint = "/fapi/v1/klines" if self.futures else "/api/v3/klines"
        raw_candles = self._make_request(endpoint, params)
        candles = []
        Candle = namedtuple("Candle", " time_stamp open high low close vol")
        if raw_candles is not None:
            for c in raw_candles:
                candles.append(Candle(c[0], float(c[1]), float(c[2]), float(c[3]), float(c[4]), float(c[5])))
            return candles
        else:
            return None
