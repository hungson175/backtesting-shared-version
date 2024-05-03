import logging
import time
import typing

import utils
from database import Hdf5Client
from exchanges import BinanceClient
from utils import *


def collect_all(client: typing.Union[BinanceClient], exchange: str, symbol: str, interval="1m"):
    h5_db = Hdf5Client(exchange=exchange)
    h5_db.create_dataset(symbol)

    # data = h5_db.get_data(symbol, from_time=0, to_time=int(time.time()*1000))
    # data = resample_timeframe(data, "1d")
    # print(data)
    # return

    oldest_ts, most_recent_ts = h5_db.get_first_last_timestamp(symbol)
    # print(oldest_ts, most_recent_ts)

    # Initial request

    if oldest_ts is None:
        data = client.get_historical_data(symbol, end_time=int(time.time()) * 1000 - 60000, interval=interval)
        if len(data) == 0:
            logger.warning("%s %s : no initial data found", exchange, symbol, )
            return
        else:
            logger.info("%s %s: Collected %s initial data from %s to %s", exchange, symbol, len(data),
                        ms_to_dt(data[0].time_stamp), ms_to_dt(data[-1].time_stamp))
        oldest_ts = data[0].time_stamp
        most_recent_ts = data[-1].time_stamp
        # Insert the data to DB
        h5_db.write_data(symbol=symbol, data=data)

    # Most recent data
    logger.info("Getting most recent data")
    data_to_insert = []
    while True:
        data = client.get_historical_data(symbol=symbol, start_time=most_recent_ts + 60 * 1000)
        if data is None:
            logger.info("Request error somehow, waiting for 4s to reconnect...")
            time.sleep(4)  # pause in case an error occurs
            continue

        # logger.info("Data is not none with len = %s", len(data))
        if len(data) < 2:
            break

        data = data[:-1]
        data_to_insert += data
        if len(data_to_insert) > 10000:
            h5_db.write_data(symbol, data_to_insert)
            data_to_insert.clear()

        if data[-1].time_stamp > most_recent_ts:
            most_recent_ts = data[-1].time_stamp
            logger.info("%s %s: Collected %s recent data from %s to %s", exchange, symbol, len(data),
                        ms_to_dt(data[0].time_stamp), ms_to_dt(data[-1].time_stamp))

        logger.info("Pause for 1.1s before request more data (counter spam)")
        h5_db.write_data(symbol, data)
        time.sleep(1.1)

    h5_db.write_data(symbol, data_to_insert)

    # Older data
    logger.info("Getting older data")
    while True:
        data = client.get_historical_data(symbol=symbol, end_time=int(oldest_ts) - 60 * 1000)
        if data is None:
            logger.info("Request error somehow, waiting for 4s to reconnect...")
            time.sleep(4)  # pause in case an error occurs
            continue

        if len(data) == 0:
            logging.info("%s %s: Stopped older collection, no data found before %s"
                         , exchange, symbol, ms_to_dt(oldest_ts))
            break
        data_to_insert += data
        if len(data_to_insert) > 10000:
            h5_db.write_data(symbol, data_to_insert)
            data_to_insert.clear()

        if data[0].time_stamp < oldest_ts:
            oldest_ts = data[0].time_stamp
            logger.info("%s %s: Collected %s older data from %s to %s", exchange, symbol, len(data),
                        ms_to_dt(data[0].time_stamp), ms_to_dt(data[-1].time_stamp))

        h5_db.write_data(symbol, data_to_insert)

        time.sleep(1.1)
