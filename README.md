
# Backtesting system

## Description
This project is a comprehensive backtesting framework designed for evaluating and optimizing trading strategies on historical data. It is tailored to support various trading algorithms. 

## Features
- **Multiple Trading Strategies**: Support for diverse strategies, including moving average and dual moving average strategies.
- **Data Collection**: Integrated data collection from multiple exchanges.
- **Optimization Tools**: Includes tools for strategy optimization to enhance trading performance.
- **Results Analysis**: Stores backtesting results for comprehensive analysis.

## Installation
To set up this project on your local machine, follow these steps:

```bash
git clone https://github.com/yourusername/trading-system-backtester.git
cd trading-system-backtester
poetry install
```

## Usage
To run the backtester, execute the `main.py` script using Poetry:

```bash
poetry run python main.py
```
Select:
- **_0_** : for collecting data (default: BTCUSDT from Binance).<br>
**Note**: There is a minor issue where, after the initial run (which lasts several seconds), the data may not update further. Please interrupt the execution by pressing Ctrl+C on Linux, and then restart it. Initially, you may need to allow some time for the data to be fully collected. For subsequent runs, you can interrupt the process at any time. Each
- **_1_** : for backtesting a strategy (need data from 0 first)
- **_2_** : for optimizing a strategy (need data from 0 first)

## Add a new strategy
To add a new strategy, create a new Python file in the `strategies` directory. <br>


## Contact Information
- **Email**: sphamhung@gmail.com
- **Project Repository**: [GitHub](https://github.com/yourusername/trading-system-backtester)
