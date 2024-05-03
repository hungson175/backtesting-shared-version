import os
from collections import namedtuple

import numpy as np
import pandas as pd

import utils

START_BALANCE = 100
TRADE_HEADERS = "l_s entry_price exit_price trade_pnl curr_balance entry_time exit_time duration"
Trade = namedtuple("Trade", TRADE_HEADERS)


def merge_trades(ts1, ts2):
    temp_trades = ts1 + ts2
    temp_trades.sort(key=lambda x: x.exit_time)
    trades = []
    curr_balance = START_BALANCE
    for trade in temp_trades:
        d = trade._asdict()
        curr_balance += d["trade_pnl"]
        d["curr_balance"] = curr_balance
        trades.append(Trade(**d))
    return trades


def write_trading_file(file_name, trades, pnl, max_dd):
    print(f"File name: {file_name} | trades length: {len(trades)}")
    with open(file_name, "w") as file:
        print((os.path.basename(file.name)).rsplit(sep=".", maxsplit=1)[0])
        file.write(f"PNL = {pnl} | MaxDD = {max_dd}\n")
        file.write(','.join(TRADE_HEADERS.split()) + "\n")
        for trade in trades:
            file.write(','.join([str(t) for t in trade]) + "\n")


# write dataframe to a new tab in new excel file
def write_data_frame(file_name, df):
    with pd.ExcelWriter(file_name) as writer:
        df.to_excel(writer, sheet_name="Sheet1")


class TradeStrategy:
    DEFAULT_CUT_PERIOD: int = 2

    def __init__(self, data: pd.DataFrame, start_balance: int):

        self.__cut_period = TradeStrategy.DEFAULT_CUT_PERIOD

        self.df = data
        self.pnl = 0
        self.max_pnl = 0
        self.max_dd = 0
        self.trade_side = 0
        self.curr_balance = start_balance
        self.entry_price = None
        self.entry_time = None

        self.timestamp = np.array(self.df.index)
        self.close_price = np.array(self.df["close"])
        self.open_price = np.array(self.df["open"])

        self.trades = []

    def set_cut_period(self, cut_period: int):
        self.__cut_period = cut_period

    def get_cut_period(self):
        return self.__cut_period

    def _close_trade(self, i):
        exit_price = self.close_price[i]
        trade_pnl = self._compute_pnl(exit_price)
        self.pnl += trade_pnl
        self.curr_balance += trade_pnl
        self._save_trade(i, exit_price, trade_pnl)
        self.trade_side = 0
        self.entry_price = None
        self.entry_time = None

    def _compute_pnl(self, exit_price):
        return utils.compute_trade_pnl(self.curr_balance, exit_price, self.entry_price, self.trade_side)

    def _save_trade(self, i, exit_price, trade_pnl):

        self.trades.append(
            Trade(self.trade_side, self.entry_price, exit_price, trade_pnl,
                  self.curr_balance, self.entry_time + np.timedelta64(7, 'h'),
                  self.timestamp[i] + np.timedelta64(7, 'h'),
                  np.timedelta64(self.timestamp[i] - self.entry_time, 'D')))

    def _price_cut_sma(self, i, sma):
        price_cut_slow_sma = False
        for j in range(max(0, i - self.__cut_period), i + 1):
            mn, mx = min(self.open_price[j], self.close_price[j]), max(self.open_price[j], self.close_price[j])
            if mn <= sma[j] <= mx:
                price_cut_slow_sma = True
                break
        return price_cut_slow_sma
