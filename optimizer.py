import copy
import multiprocessing
import random
import typing

import utils
from database import Hdf5Client
from models import BacktestResult
from utils import STRAT_PARAMS, resample_timeframe, get_library

from strategies import *



class Eval_Process(multiprocessing.Process):
    def __init__(self, bt: BacktestResult, optimizer):
        multiprocessing.Process.__init__(self)
        self.bt = bt
        self.pnl = multiprocessing.Value('f', -float("inf"))
        self.max_dd = multiprocessing.Value('f', float("inf"))
        self.optimizer = optimizer

    def run(self):
        self.pnl.value, self.max_dd.value = self.optimizer.eval_backtest(self.bt)
        # print(f"In process {os.getpid()} PNL = {self.pnl}, MAX_DD = {self.max_dd}")


class Nsga2:
    def __init__(self, exchange: str, symbol: str, strategy: str, tf: str, from_time: int, to_time: int,
                 population_size: int, min_required_trades: int):
        self.exchange = exchange
        self.symbol = symbol
        self.strategy = strategy
        self.tf = tf
        self.from_time = from_time
        self.to_time = to_time
        self.population_size = population_size
        self.min_required_trades = min_required_trades
        self.population_params = []

        self.params_data = STRAT_PARAMS[strategy]

        if self.strategy in ['sma_dual_long', 'sma_dual_short', 'sep_strat_sma_dual']:
            h5_db = Hdf5Client(exchange)
            self.data = h5_db.get_data(symbol, from_time, to_time)
            self.data = resample_timeframe(self.data, tf)
        elif self.strategy in ['psar', 'sma']:
            self.lib = get_library()
            if self.strategy == 'sma':
                self.obj = self.lib.Sma_new(exchange.encode(), symbol.encode(), tf.encode(), from_time, to_time)
            elif self.strategy == 'psar':
                self.obj = self.lib.Psar_new(exchange.encode(), symbol.encode(), tf.encode(), from_time, to_time)

    def create_initial_population(self) -> typing.List[BacktestResult]:
        population = []

        while len(population) < self.population_size:
            backtest = BacktestResult()
            for p_code, p in self.params_data.items():
                if p["type"] == int:
                    backtest.parameters[p_code] = random.randint(p["min"], p["max"])
                elif p["type"] == float:
                    backtest.parameters[p_code] = round(random.uniform(p["min"], p["max"]), p["decimals"])
            if backtest not in population:
                population.append(backtest)
                self.population_params.append(backtest.parameters)

        return population

    def crowding_distance(self, population: typing.List[BacktestResult]) -> typing.List[BacktestResult]:
        for objective in ['pnl', 'max_dd']:
            population = sorted(population, key=lambda x: getattr(x, objective))
            min_value = getattr(min(population, key=lambda x: getattr(x, objective)), objective)
            max_value = getattr(max(population, key=lambda x: getattr(x, objective)), objective)

            population[0].crowding_distance = float("inf")
            population[-1].crowding_distance = float("inf")
            max_dist = max_value - min_value
            for i in range(1, len(population) - 1):
                distance = getattr(population[i + 1], objective) - getattr(population[i - 1], objective)
                if max_dist < 1e-9:
                    distance = 0
                else:
                    distance = distance / max_dist
                population[i].crowding_distance += distance

        return population

    def eval_backtest(self, bt: BacktestResult):
        # if self.strategy == "obv":
        #     bt.pnl, bt.max_dd = strategies.depricated.obv.backtest(self.data, bt.parameters["ma_period"])
        if self.strategy == 'sma_dual_long':
            st = sma_dual_ls.SMA_Dual_LS(
                self.data,
                1,
                bt.parameters["slow_ma_period"],
                bt.parameters["fast_ma_period"],
                bt.parameters["entry_pct"],
                bt.parameters["tolerance_pct"],
            )
            bt.pnl, bt.max_dd, trades = st.backtest()
            if len(trades) < self.min_required_trades:
                bt.pnl, bt.max_dd = 0, 0

        elif self.strategy == 'sma_dual_short':
            st = sma_dual_ls.SMA_Dual_LS(
                self.data,
                -1,
                bt.parameters["slow_ma_period"],
                bt.parameters["fast_ma_period"],
                bt.parameters["entry_pct"],
                bt.parameters["tolerance_pct"],
            )
            bt.pnl, bt.max_dd, trades = st.backtest()
            if len(trades) < self.min_required_trades:
                bt.pnl, bt.max_dd = 0, 0
        elif self.strategy == "sep_strat_sma_dual":
            st = sep_strat_sma_dual.Sep_Strat_SMA_Dual(
                self.data, bt.parameters["long_pct"],
                bt.parameters["long_slow_ma_period"],
                bt.parameters["long_fast_ma_period"],
                bt.parameters["long_entry_pct"],
                bt.parameters["long_tolerance_pct"],

                bt.parameters["short_slow_ma_period"],
                bt.parameters["short_fast_ma_period"],
                bt.parameters["short_entry_pct"],
                bt.parameters["short_tolerance_pct"],

            )
            bt.pnl, bt.max_dd, trades = st.backtest()
            if len(trades) < self.min_required_trades:
                bt.pnl, bt.max_dd = 0, 0
        elif self.strategy == "sma":
            self.lib.Sma_execute_backtest(self.obj, bt.parameters["slow_ma"], bt.parameters["fast_ma"])
            bt.pnl = self.lib.Sma_get_pnl(self.obj)
            bt.max_dd = self.lib.Sma_get_max_dd(self.obj)

        if bt.pnl == 0:
            bt.pnl = -float("inf")
            bt.max_dd = float("inf")
        return bt.pnl, bt.max_dd

    def evaluate_population(self, population: typing.List[BacktestResult], multi_processed: bool = True) -> typing.List[
        BacktestResult]:
        if multi_processed:
            processes = []
            for bt in population:
                proc = Eval_Process(bt, self)
                processes.append(proc)
                proc.start()
            for i in range(0, len(population)):
                processes[i].join()
                bt = population[i]
                bt.pnl = processes[i].pnl.value
                bt.max_dd = processes[i].max_dd.value
        else:
            for bt in population:
                self.eval_backtest(bt)
        return population

    def create_new_population(self, fronts: typing.List[typing.List[BacktestResult]]) -> typing.List[BacktestResult]:
        new_pop = []
        for front in fronts:
            if len(new_pop) + len(front) > self.population_size:
                max_individuals = self.population_size - len(new_pop)
                if max_individuals > 0:
                    new_pop += sorted(front, key=lambda x: getattr(x, "crowding_distance"))[-max_individuals:]
            else:
                new_pop += front
        return new_pop

    def create_offspring_population(self, population):
        offspring_pop = []
        while len(offspring_pop) != self.population_size:
            parents: typing.List[BacktestResult] = []
            for i in range(2):
                random_parents = random.sample(population, k=2)
                if random_parents[0].rank != random_parents[1].rank:
                    best_parent = min(random_parents, key=lambda x: getattr(x, "rank"))
                else:
                    best_parent = max(random_parents, key=lambda x: getattr(x, "crowding_distance"))
                parents.append(best_parent)

            new_child = BacktestResult()
            new_child.parameters = copy.copy(parents[0].parameters)

            # Crossover
            numbers_of_crossovers = random.randint(1, len(self.params_data))
            params_to_cross = random.sample(list(self.params_data), k=numbers_of_crossovers)
            for p in params_to_cross:
                new_child.parameters[p] = copy.copy(parents[1].parameters[p])

            # Mutation
            numbers_of_mutation = random.randint(0, len(self.params_data))
            params_to_change = random.sample(list(self.params_data), k=numbers_of_mutation)
            for p in params_to_change:
                mutation_strength = random.uniform(-2, 2)
                new_child.parameters[p] = self.params_data[p]["type"](new_child.parameters[p] * (1 + mutation_strength))
                new_child.parameters[p] = max(new_child.parameters[p], self.params_data[p]["min"])
                new_child.parameters[p] = min(new_child.parameters[p], self.params_data[p]["max"])

                if self.params_data[p]["type"] == float:
                    new_child.parameters[p] = round(new_child.parameters[p], self.params_data[p]["decimals"])
            new_child.parameters = self._params_constraints(new_child.parameters)
            # print("New child params: ",new_child.parameters)
            if new_child.parameters not in self.population_params:
                offspring_pop.append(new_child)
                self.population_params.append(new_child.parameters)

        return offspring_pop

    def _params_constraints(self, params: typing.Dict) -> typing.Dict:
        if self.strategy == 'obv':
            pass
        elif self.strategy == 'sma_dual_short':
            params['fast_ma_period'] = min(params['slow_ma_period'] // 2, params['fast_ma_period'])
        elif self.strategy == 'sma_dual_long':
            params['fast_ma_period'] = min(params['slow_ma_period'] // 2, params['fast_ma_period'])
        elif self.strategy == 'sep_strat_sma_dual':
            params['long_fast_ma_period'] = min(params['long_slow_ma_period'] // 2, params['long_fast_ma_period'])
            params['short_fast_ma_period'] = min(params['short_slow_ma_period'] // 2, params['short_fast_ma_period'])
        return params

    def non_dominated_sorting(self, population: typing.Dict[int, BacktestResult]) \
            -> typing.List[typing.List[BacktestResult]]:
        fronts = []

        for id_1, indiv_1 in population.items():
            for id_2, indiv_2 in population.items():
                if indiv_1.pnl >= indiv_2.pnl and indiv_1.max_dd <= indiv_2.max_dd and \
                        (indiv_1.pnl > indiv_2.pnl or indiv_1.max_dd < indiv_2.max_dd):
                    indiv_1.dominates.append(id_2)
                elif indiv_2.pnl >= indiv_1.pnl and indiv_2.max_dd <= indiv_1.max_dd and \
                        (indiv_2.pnl > indiv_1.pnl or indiv_2.max_dd < indiv_1.max_dd):
                    indiv_1.dominated_by += 1

            if indiv_1.dominated_by == 0:
                if len(fronts) == 0:
                    fronts.append([])
                fronts[0].append(indiv_1)
                indiv_1.rank = 0

        i = 0
        while True:
            fronts.append([])
            for indiv_1 in fronts[i]:
                for indiv_2_id in indiv_1.dominates:
                    population[indiv_2_id].dominated_by -= 1
                    if population[indiv_2_id].dominated_by == 0:
                        fronts[i + 1].append(population[indiv_2_id])
                        population[indiv_2_id].rank = i + 1
            if len(fronts[i + 1]) > 0:
                i += 1
            else:
                del fronts[-1]
                break

        return fronts
