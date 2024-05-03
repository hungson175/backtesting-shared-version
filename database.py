
import time
from typing import NamedTuple, List, Union, Tuple
from utils import logger
import numpy as np
import pandas as pd

import h5py

from utils import Candle

class Hdf5Client:
    # def __int__(self, exchange: str):
    #     self.hf = h5py.File(f"data/{exchange}.h5", "a")
    #     self.hf.flush()
    def __init__(self, exchange: str):
        self.hf = h5py.File(f"data/{exchange}.h5", 'a')
        self.hf.flush()

    def create_dataset(self, symbol: str):
        if symbol not in self.hf.keys():
            logger.info("Creating data set %s", symbol)
            self.hf.create_dataset(symbol, shape=(0, 6), maxshape=(None, 6), dtype="float64")
            self.hf.flush()

    def get_data(self, symbol: str, from_time: int, to_time: int) -> Union[None, pd.DataFrame]:
        start_query = time.time()

        # TODO: why [:], what if I took it away ?
        existing_data = self.hf[symbol][:]

        if len(existing_data) == 0:
            return None

        data = sorted(existing_data, key=lambda x: x[0])
        data = np.array(data)

        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = df[(df["timestamp"] >= from_time) & (df["timestamp"] <= to_time)]

        df["timestamp"] = pd.to_datetime(df["timestamp"].values.astype(np.int64), unit="ms")
        df.set_index("timestamp", drop=True, inplace=True)  # inplace=True -> just reassigning df

        query_time = round((time.time() - start_query), 2)
        logger.info("Retrieved %s %s data from database in %s seconds", symbol, len(df), query_time)

        return df

    def write_data(self, symbol: str, data: List[Tuple]):
        logger.info("Writing data symbol = %s", symbol)
        n_existing_rows = self.hf[symbol].shape[0]

        # TODO: play around, what happens to np.array if the underlying list is changed ?
        # The real question is: np.array create a new copy or just "pointer" the existing data ?
        min_ts, max_ts = self.get_first_last_timestamp(symbol)
        if min_ts is None:
            min_ts = float("inf")
            max_ts = 0
        # TODO: after running okie, change to namedtuple notion, see if it helps
        filtered_data = list(filter(lambda d: d[0] < min_ts or d[0] > max_ts, data))
        if len(filtered_data) == 0:
            logger.info("No new data, nothing to write for symbol %s", symbol)
            return

        data_array = np.array(filtered_data)

        self.hf[symbol].resize(n_existing_rows + data_array.shape[0], axis=0)
        self.hf[symbol][-data_array.shape[0]:] = data_array

        self.hf.flush()

    def get_first_last_timestamp(self, symbol: str) -> Union[Tuple[None, None], Tuple[float, float]]:
        existing_data = self.hf[symbol][:]
        if len(existing_data) == 0:
            return None, None
        first_ts = min(existing_data, key=lambda x: x[0])[0]
        last_ts = max(existing_data, key=lambda x: x[0])[0]

        return int(first_ts), int(last_ts)
