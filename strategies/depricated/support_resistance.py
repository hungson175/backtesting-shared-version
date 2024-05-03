import time

import numpy as np
from utils import *

START_BALANCE = 100
MIN_REQUIRED_TRADES = 10
COUNT_PENETRATING = 5

# matplotlib.use('TkAgg')
pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 1000)
pd.set_option("display.width", 1000)
FEE = 0.038  # 0.05% trading fee - once sell/once buy = 0.1%


def backtest(df: pd.DataFrame, min_points: int, min_diff_points: int, rounding_nb: int, stop_loss: float,
             take_profit: float, file_name: str = None):
    RES = "resistances"
    SUPP = "supports"

    pnl = 0
    trade_side = 0  # -1 : short, 1: long
    entry_price = None
    entry_time = None
    max_pnl, max_dd = 0, 0

    candle_length = df.iloc[1].name - df.iloc[0].name
    df["rounded_high"] = round(df["high"] / rounding_nb) * rounding_nb
    df["rounded_low"] = round(df["low"] / rounding_nb) * rounding_nb

    prices_groups = {SUPP: dict(), RES: dict()}
    levels = {SUPP: [], RES: []}
    last_h_l = {SUPP: [], RES: []}
    res_supp = {SUPP: [], RES: []}

    Trade = namedtuple("Trade", "l_s entry_price exit_price entry_time exit_time")
    trades = []
    curr_balance = START_BALANCE

    start_time = time.time() * 1000

    highs = np.array(df["high"])
    lows = np.array(df["low"])
    rounded_highs = np.array(df["rounded_high"])
    rounded_lows = np.array(df["rounded_low"])
    closes = np.array(df["close"])
    times = np.array(df.index)
    # row = {"high": highs, "low": lows, "rounded_high": rounded_highs, "rounded_low": rounded_low, "close": closes}

    # for index, row in df.iterrows():
    for i in range(len(highs)):
        index = times[i]
        row = {'high': highs[i], 'low': lows[i],
               'rounded_high': rounded_highs[i], 'rounded_low': rounded_lows[i],
               'close': closes[i]}
        for side in [RES, SUPP]:
            h_l = "high" if side == RES else "low"
            if row["rounded_" + h_l] in prices_groups[side]:
                grp = prices_groups[side][row["rounded_" + h_l]]

                if grp["start_time"] is None:
                    broken_in_last = 0
                    for c in last_h_l[side]:
                        if c > row[h_l] and side == RES:
                            broken_in_last += 1
                        if c < row[h_l] and side == SUPP:
                            broken_in_last += 1
                    if broken_in_last < COUNT_PENETRATING:
                        grp["start_time"] = index

                if broken_in_last < COUNT_PENETRATING and (
                        grp["last"] is None or index >= grp["last"] + min_diff_points * candle_length):
                    grp["prices"].append(row[h_l])
                    if len(grp["prices"]) >= min_points:
                        extreme_price = max(grp["prices"]) if side == RES else min(grp["prices"])
                        levels[side].append([(grp["start_time"], extreme_price), (index, extreme_price)])
                        res_supp[side].append({"price": extreme_price, "broken": False})
                    grp["last"] = index

            else:
                broken_in_last = 0
                for c in last_h_l[side]:
                    if c > row[h_l] and side == RES:
                        broken_in_last += 1
                    if c < row[h_l] and side == SUPP:
                        broken_in_last += 1

                if broken_in_last < COUNT_PENETRATING:
                    prices_groups[side][row["rounded_" + h_l]] = {"prices": [row[h_l]], "start_time": index,
                                                                  "last": index}

            # Check whether the price groups are still valid or not
            for key, value in prices_groups[side].items():
                if len(value["prices"]) > 0:
                    if side == RES and row[h_l] > max(value["prices"]):
                        value["prices"].clear()
                        value["start_time"] = None
                        value["last"] = None
                    elif side == SUPP and row[h_l] < min(value["prices"]):
                        value["prices"].clear()
                        value["start_time"] = None
                        value["last"] = None
            last_h_l[side].append(row[h_l])
            if len(last_h_l[side]) > 10:
                last_h_l[side].pop(0)

            # Check new trade

            for sup_res in res_supp[side]:
                entry_condition = row["close"] > sup_res["price"] if side == RES else row['close'] < sup_res['price']
                if entry_condition and not sup_res["broken"]:
                    sup_res["broken"] = True
                if trade_side == 0:
                    entry_price = row["close"]
                    trade_side = 1 if side == RES else -1
                    entry_time = index

            # Check PNL

            if trade_side == 1:
                if row["close"] >= entry_price * (1 + take_profit / 100) or row["close"] <= entry_price * (
                        1 - stop_loss / 100):
                    # pnl += ((row["close"] / entry_price - 1) * 100 - 2 * FEE)
                    entry_quant = (curr_balance / entry_price) * (1 - FEE / 100)
                    exit_sum = entry_quant * row["close"] * (1 - trade_side * FEE / 100)
                    trade_pnl = trade_side * (exit_sum - curr_balance)
                    curr_balance += trade_pnl
                    pnl += trade_pnl
                    trades.append(Trade(trade_side, entry_price, row["close"], entry_time, index))
                    trade_side = 0
                    entry_price = None
                    entry_time = None

            if trade_side == -1:
                if row["close"] <= entry_price * (1 - take_profit / 100) or row["close"] >= entry_price * (
                        1 + stop_loss / 100):
                    # pnl += ((entry_price / row["close"] - 1) * 100 - 2 * FEE)
                    # curr_balance *= (entry_price / row["close"] - 1 - 2 * FEE / 100)
                    entry_quant = (curr_balance / entry_price) * (1 - FEE / 100)
                    exit_sum = entry_quant * row["close"] * (1 - trade_side * FEE / 100)
                    trade_pnl = trade_side * (exit_sum - curr_balance)
                    curr_balance += trade_pnl
                    pnl += trade_pnl

                    trades.append(Trade(trade_side, entry_price, row["close"], entry_time, index))
                    trade_side = 0
                    entry_price = None
                    entry_time = None
            max_pnl = max(max_pnl, pnl)
            max_dd = max(max_dd, max_pnl - pnl)

    if len(trades) < MIN_REQUIRED_TRADES:
        pnl = -float("inf")
        max_dd = float("inf")
    logger.info(
        f"Finish support/resistance back-test  for timeframe after {round(time.time() * 1000 - start_time, 0)}ms | PNL =  {round(pnl, 2)} | Max.DD = {round(max_dd, 2)}")

    # mpf.plot(df, type="candle", style="charles", alines=dict(alines=levels[RES] + levels[SUPP]))
    # plt.show(block=False)
    #     if store_trades:
    #         # file.writelines(trades)
    #         file.write(",".join((str(START_BALANCE), str(curr_balance))) + "\n")
    #         for trade in trades:
    #             file.write(','.join([str(t) for t in trade]) + "\n")
    #
    #
    # if not store_trades:
    #     os.remove(file_name)

    if file_name is not None:
        print(file_name)
        with open(file_name, "w") as file:
            file.write(
                f"mpoints={min_points}, min_diff_points={min_diff_points}, rounding_nb={round(rounding_nb, 2)}, tp={take_profit}, sl={stop_loss}\n")
            file.write(f"PNL = {pnl} | MaxDD = {max_dd}\n")
            for trade in trades:
                file.write(','.join([str(t) for t in trade]) + "\n")

    return pnl, max_dd
