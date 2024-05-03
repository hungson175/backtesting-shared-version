import pandas as pd
from binance.spot import Spot
import exchanges.binance as binance

client = binance.BinanceClient()
time = client.time()
print(time, pd.to_datetime(time, unit="ms"))

candles = client.get_historical_data(symbol="BTCUSDT", interval="4h")
print(len(candles))
print(pd.to_datetime(candles[0].time_stamp, unit='ms'), candles[0])
print(pd.to_datetime(candles[-1].time_stamp, unit='ms'), candles[-1])

print(f"current price: {client.get_current_price('BTCUSDT')}")
closes = [candle.close for candle in candles]
timestamps = [candle.time_stamp for candle in candles]
# convert to pandas dataframe with 2 columns: timestamp and close
df = pd.DataFrame({"timestamp": timestamps, "close": closes})

# df = pd.DataFrame({timestamps, closes}, columns=['timestamp', 'close'])

df['sma'] = df["close"].rolling(50).mean()
# create new column with date converted from timestamp
df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
# set timestamp as index
df.set_index('date', inplace=True)
# drop timestamp column
df.drop('timestamp', axis=1, inplace=True)

print(df)
print(f"current price: {client.get_current_price('BTCUSDT')}")
# read most recent 1m candlestick data for BTCUSDT
# client = Spot()
# print(client.time())
# print(pd.to_datetime(client.time()['serverTime'], unit="ms"))
# lst = client.klines("BTCUSDT", "1m")
