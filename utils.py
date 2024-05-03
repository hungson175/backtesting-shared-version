import datetime
import logging
from collections import namedtuple
from ctypes import *

import pandas as pd

FEE = 0.027  # 0.03 % (0.0003)
TF_EQUIV = {"1m": "1Min", "5m": "5Min", "15m": "15Min", "30m": "30Min", "1h": "1H", "4h": "4H", "12h": "12H", "1d": "D",
            "1w": "W"}
Candle = namedtuple("Candle", " time_stamp open high low close vol")
logger = logging.getLogger("sonph_bt")

STRAT_PARAMS = {
    "sma_dual_long": {
        "slow_ma_period": {"name": "Slow MA period", "type": int, "min": 20, "max": 200},
        "fast_ma_period": {"name": "Fast MA period", "type": int, "min": 7, "max": 50},
        "entry_pct": {"name": "Entry tolerance percentage", "type": float, "min": 0.001, "max": 0.03, "decimals": 3},
        "tolerance_pct": {"name": "Exit tolerance percentage", "type": float, "min": 0.001, "max": 0.03, "decimals": 3},
    },

    "sma_dual_short": {
        "slow_ma_period": {"name": "Slow MA period", "type": int, "min": 20, "max": 200},
        "fast_ma_period": {"name": "Fast MA period", "type": int, "min": 7, "max": 50},
        "entry_pct": {"name": "Entry tolerance percentage", "type": float, "min": 0.001, "max": 0.04, "decimals": 3},
        "tolerance_pct": {"name": "Exit tolerance percentage", "type": float, "min": 0.001, "max": 0.04, "decimals": 3},
    },

    "sep_strat_sma_dual": {
        "long_pct": {"name": "Long strategy percetage", "type": int, "min": 30, "max": 70},
        "long_slow_ma_period": {"name": "Slow MA period", "type": int, "min": 20, "max": 200},
        "long_fast_ma_period": {"name": "Fast MA period", "type": int, "min": 7, "max": 100},
        "long_entry_pct": {"name": "Entry tolerance percentage", "type": float, "min": 0.001, "max": 0.04, "decimals": 3},
        "long_tolerance_pct": {"name": "Exit tolerance percentage", "type": float, "min": 0.001, "max": 0.04, "decimals": 3},
        "short_slow_ma_period": {"name": "Slow MA period", "type": int, "min": 20, "max": 200},
        "short_fast_ma_period": {"name": "Fast MA period", "type": int, "min": 7, "max": 100},
        "short_entry_pct": {"name": "Entry tolerance percentage", "type": float, "min": 0.001, "max": 0.04, "decimals": 3},
        "short_tolerance_pct": {"name": "Exit tolerance percentage", "type": float, "min": 0.001, "max": 0.04,"decimals": 3},

    },

}


def ms_to_dt(ms: int):
    return datetime.datetime.utcfromtimestamp(ms / 1000)


# convert date string to milliseconds
def date_to_ms(date_str: str, date_format='%Y/%m/%d') -> int:
    return int(datetime.datetime.strptime(date_str, date_format).timestamp()) * 1000


def resample_timeframe(data: pd.DataFrame, tf: str) -> pd.DataFrame:
    return data.resample(TF_EQUIV[tf]).agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    )


def get_library():
    lib = CDLL("backtesting_cpp/cmake-build-debug/libbacktestingCpp.so", winmode=0)

    # SMA
    lib.Sma_new.restype = c_void_p
    lib.Sma_new.argtypes = [c_char_p, c_char_p, c_char_p, c_longlong, c_longlong]

    lib.Sma_execute_backtest.restype = c_void_p
    lib.Sma_execute_backtest.argtypes = [c_void_p, c_int, c_int]

    lib.Sma_get_pnl.restype = c_double
    lib.Sma_get_pnl.argtypes = [c_void_p]
    lib.Sma_get_max_dd.restype = c_double
    lib.Sma_get_max_dd.argtypes = [c_void_p]

    # PSAR

    lib.Psar_new.restype = c_void_p
    lib.Psar_new.argtypes = [c_char_p, c_char_p, c_char_p, c_longlong, c_longlong]

    lib.Psar_execute_backtest.restype = c_void_p
    lib.Psar_execute_backtest.argtypes = [c_void_p, c_double, c_double, c_double]

    lib.Psar_get_pnl.restype = c_double
    lib.Psar_get_pnl.argtypes = [c_void_p]
    lib.Psar_get_max_dd.restype = c_double
    lib.Psar_get_max_dd.argtypes = [c_void_p]

    return lib


def compute_trade_pnl(curr_balance, exit_price, entry_price, trade_side):
    entry_quant = (curr_balance / entry_price) * (1 - FEE / 100)
    exit_sum = entry_quant * exit_price * (1 - trade_side * FEE / 100)
    trade_pnl = trade_side * (exit_sum - curr_balance)
    return trade_pnl

# compute pnl and max dd from trades
def compute_pnl_maxdd(trades):
    pnl = 0
    max_dd = 0
    max_pnl = 0
    curr_balance = 100
    for trade in trades:
        pnl += trade.trade_pnl
        curr_balance += trade.trade_pnl
        max_pnl = max(max_pnl, pnl)
        max_dd = max(max_dd, max_pnl - pnl)
    return pnl, max_dd

# write dataframe to posgresql database with given username and password
def write_df_to_db(df, table_name, username, password):
    engine = create_engine(f"postgresql://{username}:{password}@localhost:5432/crypto")
    df.to_sql(table_name, engine, if_exists='replace', index=False)