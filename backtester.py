import strategies
import utils
from strategies import trade_strategy, single_ma_long
from database import Hdf5Client
from utils import resample_timeframe, logger


def run(exchange: str, symbol: str, strategy: str, tf: str, from_time: int, to_time: int):
    # params_des = STRAT_PARAMS[strategy]
    # params = dict()
    # for p_code, p in params_des.items():
    #     while True:
    #         try:
    #             params[p_code] = p["type"](input(p["name"] + ": "))
    #             break
    #         except ValueError:
    #             continue

    from_time_str = str(utils.ms_to_dt(from_time)).split(' ')[0]
    to_time_str = str(utils.ms_to_dt(to_time)).split(' ')[0]
    file_prefix = f"results/trade_{symbol}_{strategy}_{tf}_fr{from_time_str}_to{to_time_str}"

    logger.info("Run backtesting for %s/%s - strat: %s / %s - from %s to %s", exchange, symbol, strategy, tf,
                utils.ms_to_dt(from_time), utils.ms_to_dt(to_time))

    h5_db = Hdf5Client(exchange)
    data = h5_db.get_data(symbol, from_time=from_time, to_time=to_time)
    data = resample_timeframe(data, tf)

    # # Research direction: observe both the long/short strategies and find out which period both
    # # strategies are unprofitable, then find out the signals that are generated during that period
    # # (for 4h candles) - then try to find a  profitable range-trading strategy for that period
    if strategy == 'single_ma_long':
        ma_period = 50
        entry_pct = 0.001
        tolerance_pct = 0.001

        file_name = (file_prefix
                     + f"_ma{ma_period}"
                     + f"cp{2}_spct{entry_pct}_tpct{tolerance_pct}"
                     + ".csv")

        st = strategies.single_ma_long.SingleMALong(data, ma_period, entry_pct, tolerance_pct)
        pnl, max_dd, trades = st.backtest()
        trade_strategy.write_trading_file(file_name, trades, pnl, max_dd)
        return pnl, max_dd
