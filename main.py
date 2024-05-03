import backtester
import optimizer
from data_collector import *

logger = logging.getLogger("sonph_bt")
logger.setLevel(logging.DEBUG)
optimize_result_logger = logging.getLogger("sonph_tunning_result")
optimize_result_logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s %(levelname)s :: %(message)s")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

file_handler = logging.FileHandler("./info.log")
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.DEBUG)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

logger.log(logging.INFO, "Main application started at %s", datetime.datetime.utcnow())

tune_file_handler = logging.FileHandler("./tuning_results.txt")
tune_file_handler.setFormatter(formatter)
tune_file_handler.setLevel(logging.DEBUG)
optimize_result_logger.addHandler(tune_file_handler)


def run_optimize(title: str, multi_processed: bool = True):
    start_time = time.time() * 1000
    p_population = nsga2.create_initial_population()
    p_population = nsga2.evaluate_population(p_population, multi_processed=multi_processed)
    p_population = nsga2.crowding_distance(p_population)
    g = 0
    while g < generations:
        q_population = nsga2.create_offspring_population(p_population)
        q_population = nsga2.evaluate_population(q_population, multi_processed=multi_processed)

        r_population = p_population + q_population
        nsga2.population_params.clear()

        i = 0
        population = dict()
        for bt in r_population:
            bt.reset_results()
            nsga2.population_params.append(bt.parameters)
            population[i] = bt
            i += 1
        fronts = nsga2.non_dominated_sorting(population)
        for j in range(len(fronts)):
            fronts[j] = nsga2.crowding_distance(fronts[j])

        p_population = nsga2.create_new_population(fronts)

        print(f"\r{int(int(g + 1) / generations * 100)}% - generation: {g}", end='')
        g += 1
    print('\n')
    duration = int(round(time.time() * 1000 - start_time, 0))
    logger.info(title)
    optimize_result_logger.info("\n" + title)
    logger.info("Duration : %dms ", duration)
    optimize_result_logger.info("Duration : %dms ", duration)

    for individual in p_population:
        logger.info(individual)
        optimize_result_logger.info(individual)
        # print('\n'.join([str(f) for f in front]) + '\n\n')


if __name__ == '__main__':
    options = ['data', 'backtest', 'optimize']
    # mode = input("Choose the program mod: (\n\t0.data\n\t1.backtest\n\t2.optimize)\n").lower()
    print("Choose the program mod: \n\t0.data\n\t1.backtest\n\t2.optimize\n")
    # while True:
    #     exchange = input("Choose an exchange: ").lower()
    #     if exchange in ["ftx","binance"]:
    #         break
    while True:
        op = int(input())
        if 0 <= op < len(options):
            mode = options[op]
            break

    # if exchange == "binance":
    #     client = BinanceClient(futures=True)
    # elif exchange == "ftx":
    #     client = FTXClient()
    # mode = "backtest"
    if mode == "data":
        client = BinanceClient(futures=True)
        collect_all(client, exchange="Binance", symbol="BTCUSDT", interval="1m")
    elif mode == "backtest":
        strategy = "single_ma_long"
        time_frame = "4h"
        pnl, max_dd = backtester.run(exchange="Binance", symbol="BTCUSDT", strategy=strategy, tf=time_frame,
                                     from_time=utils.date_to_ms("2024/01/01"),
                                     to_time=utils.date_to_ms("2024/12/31"))

        logger.info("PNL = %s , drawndown = %s", pnl, max_dd)

    elif mode == "optimize":
        symbol = "BTCUSDT"
        strategy = "single_ma_long"
        min_required_trades = 50
        time_frame = "4h"
        pop_size = 128  # 20
        generations = 64  # 20
        from_str = "2020/01/01"
        from_time = utils.date_to_ms(from_str)
        to_str = "2023/05/01"
        to_time = utils.date_to_ms(to_str)

        nsga2 = optimizer.Nsga2("Binance",
                                symbol, strategy, time_frame, from_time, to_time,
                                pop_size, min_required_trades)
        title = f"{symbol} | {strategy}|{time_frame} | {from_str} to: {to_str} | pop_size {pop_size} | generations {generations}"
        run_optimize(title)
