import time
from collections import namedtuple

import pandas as pd
import numpy as np

import utils
from utils import compute_trade_pnl


MIN_REQUIRED_TRADE = 10


# stop_loss_pct/take_profit_pct to total amount of consecutive gain/decrease
def backtest(df: pd.DataFrame, count_consecutive: int,
             stop_loss_pct: float, take_profit_pct: float,
             file_name: str = None):
    # no fee first, then get fee in later on

    pnl = 0
    max_pnl, max_dd = 0, 0

    amount = 0
    trade_side = 0
    entry_price = None
    entry_time = None
    stop_loss_price, take_profit_price = None, None
    curr_balance = utils.START_BALANCE

    start_time = time.time() * 1000

    df["diff"] = df["close"].diff()
    df["compare_prev"] = np.where(df["diff"] == 0, 0, np.where(df["diff"] < 0, -1, 1))
    df["sum_count"] = df["compare_prev"].rolling(count_consecutive).sum().fillna(0).astype("int")
    df["sum_diff"] = df["diff"].rolling(count_consecutive).sum()
    # just for-loop first, optimize later on
    timestamp = np.array(df.index)
    close = np.array(df["close"])
    low = np.array(df["low"])
    high = np.array(df["high"])
    diff = np.array(df["diff"])
    compare_prev = np.array(df["compare_prev"])
    sum_count = np.array(df["sum_count"])
    sum_diff = np.array(df["sum_diff"])

    df.drop(columns=["diff", "compare_prev", "sum_count", "sum_diff"], axis=1,
            inplace=True)  # later, may be not neccesary

    # Trade = namedtuple("Trade", "l_s entry_price exit_price entry_time exit_time")
    Trade = namedtuple("Trade", "l_s entry_price exit_price trade_pnl entry_time exit_time duration")
    trades = []

    for i in range(0, len(df)):
        curr_price = close[i]
        if trade_side == 0:  # no position
            # gain too much, short it
            if sum_count[i] == count_consecutive:
                amount = sum_diff[i]
                trade_side = -1
                entry_price = curr_price
                stop_loss_price = entry_price + stop_loss_pct * amount
                take_profit_price = entry_price - take_profit_pct * amount
                entry_time = timestamp[i]

            # loss too much, long it
            elif sum_count[i] == -count_consecutive:
                amount = -sum_diff[i]
                trade_side = 1
                entry_price = curr_price
                stop_loss_price = entry_price - stop_loss_pct * amount
                take_profit_price = entry_price + take_profit_pct * amount
                entry_time = timestamp[i]

        elif ((trade_side == 1) and ((low[i] <= stop_loss_price) or (high[i] >= take_profit_price))) or (
                (trade_side == -1) and ((high[i] >= stop_loss_price) or (low[i] <= take_profit_price))):
            if trade_side == 1:
                if low[i] <= stop_loss_price:
                    exit_price = stop_loss_price
                else:  # high[i] >= take_profit_price
                    exit_price = take_profit_price
            if trade_side == -1:
                if high[i] >= stop_loss_price:
                    exit_price = stop_loss_price
                else:  # low[i] <= take_profit_price
                    exit_price = take_profit_price
            trade_pnl = compute_trade_pnl(curr_balance, exit_price, entry_price, trade_side)
            curr_balance += trade_pnl
            trades.append(Trade(trade_side, entry_price, exit_price, trade_pnl, entry_time, timestamp[i],
                                np.timedelta64(timestamp[i] - entry_time, 'm')))
            pnl += trade_pnl
            trade_side = 0
            entry_price = None
            entry_time = None
        else:
            pass  # should not be here
        max_pnl = max(max_pnl, pnl)
        max_dd = max(max_dd, max_pnl - pnl)

    pnl = curr_balance - utils.START_BALANCE
    # logger.info(
    #     f"Finish support/resistance back-test  for timeframe after {round(time.time() * 1000 - start_time, 0)}ms | PNL =  {round(pnl, 2)} | Max.DD = {round(max_dd, 2)}")

    if file_name is not None:
        with open(file_name, "w") as file:
            file.write(f"PNL = {pnl} | MaxDD = {max_dd}\n")
            for trade in trades:
                file.write(','.join([str(t) for t in trade]) + "\n")
    if len(trades) < MIN_REQUIRED_TRADE:
        return -float("inf"), -float("inf")
    return pnl, max_dd


