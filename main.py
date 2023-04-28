from time import sleep
from datetime import *
from indicators import *
from config import *
import pickle
import logging
import sys
from candle import Candle
from binance.spot import Spot
from credentials import *
from utils import *
from telegram_message_sender import *

is_price_increasing = False
is_price_decreasing = False
is_macd_increasing = False
is_macd_decreasing = False
is_macd_positive = False
is_macd_negative = False
account_available_balance = 0
total_account_balance = 0
is_bot_started = False
current_time = datetime.now()
indicators_dict = {}
orders_dict = {}
contract_open_orders_count = 0
open_orders_list = []
last_account_available_balances_list = []
last_total_account_balances_list = []


@retry(MAXIMUM_NUMBER_OF_API_CALL_TRIES, lambda e: logging.error(f"ERROR in update_current_time: {e}") or ERROR)
def update_current_time() -> int:
	global current_time
	global last_time
	last_time = current_time
	current_time = datetime.fromtimestamp(binance_spot_api.time()["serverTime"] / 1000)
	return SUCCESSFUL


def get_local_timestamp() -> int:
	return int(datetime.now().timestamp())


def convert_binance_data_list_to_candles_list(binance_data_list: list) -> list:
	candles_list = []
	for binance_data in binance_data_list:
		candle = Candle(datetime.fromtimestamp(binance_data[0] // 1000), binance_data[1], binance_data[2],
						binance_data[3], binance_data[4], None, datetime.fromtimestamp(binance_data[6] // 1000))
		candles_list.append(candle)
	return candles_list


def get_m1_candles(
	contract_symbol: str, 
	start_datetime: datetime, 
	end_datetime: datetime
) -> tuple:
	start_timestamp = int(start_datetime.timestamp() * 1000)
	end_timestamp = int(end_datetime.timestamp() * 1000)
	number_of_kline_candles_requests = (end_timestamp - start_timestamp + MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS - 1) // (MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS)
	all_m1_candles_list = []
	for i in range(number_of_kline_candles_requests):
		current_time_range_start = i * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS + start_timestamp
		current_time_range_end = (i + 1) * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS + start_timestamp - 1
		current_time_range_start = max(current_time_range_start, start_timestamp)
		current_time_range_start = min(current_time_range_start, end_timestamp)
		current_time_range_end = max(current_time_range_end, start_timestamp)
		current_time_range_end = min(current_time_range_end, end_timestamp)

		klines = retry(MAXIMUM_NUMBER_OF_API_CALL_TRIES, lambda e: logging.error(f"ERROR in get_m1_candles: {e}" or (ERROR, [])))(binance_spot_api.klines)
		current_time_range_m1_candles_list = klines(symbol=contract_symbol, interval="1m", startTime=current_time_range_start, endTime=current_time_range_end, limit=MAXIMUM_KLINE_CANDLES_PER_REQUEST)

		for m1_candle in current_time_range_m1_candles_list:
			all_m1_candles_list.append(Candle(datetime.fromtimestamp(m1_candle[0] // 1000),
											  m1_candle[1],
											  m1_candle[2],
											  m1_candle[3],
											  m1_candle[4],
											  m1_candle[5],
											  datetime.fromtimestamp(m1_candle[6] // 1000)))
	return (SUCCESSFUL, all_m1_candles_list)


def get_m5_candles(
	contract_symbol: str, 
	start_datetime: datetime, 
	end_datetime: datetime
) -> tuple:
	start_timestamp = int(start_datetime.timestamp() * 1000)
	end_timestamp = int(end_datetime.timestamp() * 1000)
	number_of_kline_candles_requests = (end_timestamp - start_timestamp + MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 5 - 1) // (MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 5)
	all_m5_candles_list = []
	for i in range(number_of_kline_candles_requests):
		current_time_range_start = i * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 5 + start_timestamp
		current_time_range_end = (i + 1) * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 5 + start_timestamp - 1
		current_time_range_start = max(current_time_range_start, start_timestamp)
		current_time_range_start = min(current_time_range_start, end_timestamp)
		current_time_range_end = max(current_time_range_end, start_timestamp)
		current_time_range_end = min(current_time_range_end, end_timestamp)

		klines = retry(MAXIMUM_NUMBER_OF_API_CALL_TRIES, lambda e: logging.error(f"ERROR in get_m5_candles: {e}" or (ERROR, [])))(binance_spot_api.klines)
		current_time_range_m5_candles_list = klines(symbol=contract_symbol, interval="5m", startTime=current_time_range_start, endTime=current_time_range_end, limit=MAXIMUM_KLINE_CANDLES_PER_REQUEST)

		for m5_candle in current_time_range_m5_candles_list:
			all_m5_candles_list.append(Candle(datetime.fromtimestamp(m5_candle[0] // 1000),
											  m5_candle[1],
											  m5_candle[2],
											  m5_candle[3],
											  m5_candle[4],
											  m5_candle[5],
											  datetime.fromtimestamp(m5_candle[6] // 1000)))
	return (SUCCESSFUL, all_m5_candles_list)


def get_m15_candles(
	contract_symbol: str, 
	start_datetime: datetime, 
	end_datetime: datetime
) -> tuple:
	start_timestamp = int(start_datetime.timestamp() * 1000)
	end_timestamp = int(end_datetime.timestamp() * 1000)
	number_of_kline_candles_requests = (end_timestamp - start_timestamp + MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 15 - 1) // (MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 15)
	all_m15_candles_list = []
	for i in range(number_of_kline_candles_requests):
		current_time_range_start = i * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 15 + start_timestamp
		current_time_range_end = (i + 1) * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 15 + start_timestamp - 1
		current_time_range_start = max(current_time_range_start, start_timestamp)
		current_time_range_start = min(current_time_range_start, end_timestamp)
		current_time_range_end = max(current_time_range_end, start_timestamp)
		current_time_range_end = min(current_time_range_end, end_timestamp)

		klines = retry(MAXIMUM_NUMBER_OF_API_CALL_TRIES, lambda e: logging.error(f"ERROR in get_m15_candles: {e}" or (ERROR, [])))(binance_spot_api.klines)
		current_time_range_m15_candles_list = klines(symbol=contract_symbol, interval="15m", startTime=current_time_range_start, endTime=current_time_range_end, limit=MAXIMUM_KLINE_CANDLES_PER_REQUEST)

		for m15_candle in current_time_range_m15_candles_list:
			all_m15_candles_list.append(Candle(datetime.fromtimestamp(m15_candle[0] // 1000),
											   m15_candle[1],
											   m15_candle[2],
											   m15_candle[3],
											   m15_candle[4],
											   m15_candle[5],
											   datetime.fromtimestamp(m15_candle[6] // 1000)))
	return (SUCCESSFUL, all_m15_candles_list)


def get_h1_candles(
	contract_symbol: str, 
	start_datetime: datetime, 
	end_datetime: datetime
) -> tuple:
	start_timestamp = int(start_datetime.timestamp() * 1000)
	end_timestamp = int(end_datetime.timestamp() * 1000)
	number_of_kline_candles_requests = (end_timestamp - start_timestamp + MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 - 1) // (MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60)
	all_h1_candles_list = []
	for i in range(number_of_kline_candles_requests):
		current_time_range_start = i * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 + start_timestamp
		current_time_range_end = (i + 1) * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 + start_timestamp - 1
		current_time_range_start = max(current_time_range_start, start_timestamp)
		current_time_range_start = min(current_time_range_start, end_timestamp)
		current_time_range_end = max(current_time_range_end, start_timestamp)
		current_time_range_end = min(current_time_range_end, end_timestamp)

		klines = retry(MAXIMUM_NUMBER_OF_API_CALL_TRIES, lambda e: logging.error(f"ERROR in get_h1_candles: {e}" or (ERROR, [])))(binance_spot_api.klines)
		current_time_range_h1_candles_list = klines(symbol=contract_symbol, interval="1h", startTime=current_time_range_start, endTime=current_time_range_end, limit=MAXIMUM_KLINE_CANDLES_PER_REQUEST)

		for h1_candle in current_time_range_h1_candles_list:
			all_h1_candles_list.append(Candle(datetime.fromtimestamp(h1_candle[0] // 1000),
											  h1_candle[1],
											  h1_candle[2],
											  h1_candle[3],
											  h1_candle[4],
											  h1_candle[5],
											  datetime.fromtimestamp(h1_candle[6] // 1000)))
	return (SUCCESSFUL, all_h1_candles_list)


def get_h2_candles(
	contract_symbol: str, 
	start_datetime: datetime, 
	end_datetime: datetime
) -> tuple:
	start_timestamp = int(start_datetime.timestamp() * 1000)
	end_timestamp = int(end_datetime.timestamp() * 1000)
	number_of_kline_candles_requests = (end_timestamp - start_timestamp + MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 2 - 1) // (MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 2)
	all_h2_candles_list = []
	for i in range(number_of_kline_candles_requests):
		current_time_range_start = i * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 2 + start_timestamp
		current_time_range_end = (i + 1) * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 2 + start_timestamp - 1
		current_time_range_start = max(current_time_range_start, start_timestamp)
		current_time_range_start = min(current_time_range_start, end_timestamp)
		current_time_range_end = max(current_time_range_end, start_timestamp)
		current_time_range_end = min(current_time_range_end, end_timestamp)

		klines = retry(MAXIMUM_NUMBER_OF_API_CALL_TRIES, lambda e: logging.error(f"ERROR in get_h2_candles: {e}" or (ERROR, [])))(binance_spot_api.klines)
		current_time_range_h2_candles_list = klines(symbol=contract_symbol, interval="2h", startTime=current_time_range_start, endTime=current_time_range_end, limit=MAXIMUM_KLINE_CANDLES_PER_REQUEST)

		for h2_candle in current_time_range_h2_candles_list:
			all_h2_candles_list.append(Candle(datetime.fromtimestamp(h2_candle[0] // 1000),
									   h2_candle[1],
									   h2_candle[2],
									   h2_candle[3],
									   h2_candle[4],
									   h2_candle[5],
									   datetime.fromtimestamp(h2_candle[6] // 1000)))
	return (SUCCESSFUL, all_h2_candles_list)


def get_h4_candles(
	contract_symbol: str, 
	start_datetime: datetime, 
	end_datetime: datetime
) -> tuple:
	start_timestamp = int(start_datetime.timestamp() * 1000)
	end_timestamp = int(end_datetime.timestamp() * 1000)
	number_of_kline_candles_requests = (end_timestamp - start_timestamp + MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 4 - 1) // (MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 4)
	all_h4_candles_list = []
	for i in range(number_of_kline_candles_requests):
		current_time_range_start = i * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 4 + start_timestamp
		current_time_range_end = (i + 1) * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 4 + start_timestamp - 1
		current_time_range_start = max(current_time_range_start, start_timestamp)
		current_time_range_start = min(current_time_range_start, end_timestamp)
		current_time_range_end = max(current_time_range_end, start_timestamp)
		current_time_range_end = min(current_time_range_end, end_timestamp)

		klines = retry(MAXIMUM_NUMBER_OF_API_CALL_TRIES, lambda e: logging.error(f"ERROR in get_h4_candles: {e}" or (ERROR, [])))(binance_spot_api.klines)
		current_time_range_h4_candles_list = klines(symbol=contract_symbol, interval="4h", startTime=current_time_range_start, endTime=current_time_range_end, limit=MAXIMUM_KLINE_CANDLES_PER_REQUEST)

		for h4_candle in current_time_range_h4_candles_list:
			all_h4_candles_list.append(Candle(datetime.fromtimestamp(h4_candle[0] // 1000),
											  h4_candle[1],
											  h4_candle[2],
											  h4_candle[3],
											  h4_candle[4],
											  h4_candle[5],
											  datetime.fromtimestamp(h4_candle[6] // 1000)))
	return (SUCCESSFUL, all_h4_candles_list)


def get_d1_candles(
	contract_symbol: str, 
	start_datetime: datetime, 
	end_datetime: datetime
) -> tuple:
	start_timestamp = int(start_datetime.timestamp() * 1000)
	end_timestamp = int(end_datetime.timestamp() * 1000)
	number_of_kline_candles_requests = (end_timestamp - start_timestamp + MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 24 - 1) // (MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 24)
	all_d1_candles_list = []
	for i in range(number_of_kline_candles_requests):
		current_time_range_start = i * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 24 + start_timestamp
		current_time_range_end = (i + 1) * MAXIMUM_KLINE_CANDLES_PER_REQUEST * ONE_MINUTE_IN_MILLISECONDS * 60 * 24 + start_timestamp - 1
		current_time_range_start = max(current_time_range_start, start_timestamp)
		current_time_range_start = min(current_time_range_start, end_timestamp)
		current_time_range_end = max(current_time_range_end, start_timestamp)
		current_time_range_end = min(current_time_range_end, end_timestamp)

		klines = retry(MAXIMUM_NUMBER_OF_API_CALL_TRIES, lambda e: logging.error(f"ERROR in get_d1_candles: {e}" or (ERROR, [])))(binance_spot_api.klines)
		current_time_range_d1_candles_list = klines(symbol=contract_symbol, interval="1d", startTime=current_time_range_start, endTime=current_time_range_end, limit=MAXIMUM_KLINE_CANDLES_PER_REQUEST)

		for d1_candle in current_time_range_d1_candles_list:
			all_d1_candles_list.append(Candle(datetime.fromtimestamp(d1_candle[0] // 1000),
											  d1_candle[1],
											  d1_candle[2],
											  d1_candle[3],
											  d1_candle[4],
											  d1_candle[5],
											  datetime.fromtimestamp(d1_candle[6] // 1000)))
	return (SUCCESSFUL, all_d1_candles_list)


def update_recent_prices_list(
	contract_symbol: str, 
	current_time: datetime, 
	candles_count: int,
	timeframe: str
) -> None:

	global recent_m1_open_prices_list
	global recent_m1_high_prices_list
	global recent_m1_low_prices_list
	global recent_m1_close_prices_list

	global recent_m5_open_prices_list
	global recent_m5_high_prices_list
	global recent_m5_low_prices_list
	global recent_m5_close_prices_list

	global recent_m15_open_prices_list
	global recent_m15_high_prices_list
	global recent_m15_low_prices_list
	global recent_m15_close_prices_list

	global recent_h1_open_prices_list
	global recent_h1_high_prices_list
	global recent_h1_low_prices_list
	global recent_h1_close_prices_list

	global recent_h2_open_prices_list
	global recent_h2_high_prices_list
	global recent_h2_low_prices_list
	global recent_h2_close_prices_list

	global recent_h4_open_prices_list
	global recent_h4_high_prices_list
	global recent_h4_low_prices_list
	global recent_h4_close_prices_list

	global recent_d1_open_prices_list
	global recent_d1_high_prices_list
	global recent_d1_low_prices_list
	global recent_d1_close_prices_list

	if timeframe == "m1":
		start_time = current_time - timedelta(minutes=candles_count + 10)
		end_time = current_time
		recent_candles_list = get_m1_candles(contract_symbol, start_time, end_time)[1][:-1][-candles_count:]
		recent_m1_open_prices_list = [float(candle.open) for candle in recent_candles_list]
		recent_m1_high_prices_list = [float(candle.high) for candle in recent_candles_list]
		recent_m1_low_prices_list = [float(candle.low) for candle in recent_candles_list]
		recent_m1_close_prices_list = [float(candle.close) for candle in recent_candles_list]
	if timeframe == "m5":
		start_time = current_time - timedelta(minutes=candles_count * 5 + 10)
		end_time = current_time
		recent_candles_list = get_m5_candles(contract_symbol, start_time, end_time)[1][:-1][-candles_count:]
		recent_m5_open_prices_list = [float(candle.open) for candle in recent_candles_list]
		recent_m5_high_prices_list = [float(candle.high) for candle in recent_candles_list]
		recent_m5_low_prices_list = [float(candle.low) for candle in recent_candles_list]
		recent_m5_close_prices_list = [float(candle.close) for candle in recent_candles_list]
	if timeframe == "m15":
		start_time = current_time - timedelta(minutes=(candles_count + 10) * 15)
		end_time = current_time
		recent_candles_list = get_m15_candles(contract_symbol, start_time, end_time)[1][:-1][-candles_count:]
		recent_m15_open_prices_list = [float(candle.open) for candle in recent_candles_list]
		recent_m15_high_prices_list = [float(candle.high) for candle in recent_candles_list]
		recent_m15_low_prices_list = [float(candle.low) for candle in recent_candles_list]
		recent_m15_close_prices_list = [float(candle.close) for candle in recent_candles_list]
	if timeframe == "h1":
		start_time = current_time - timedelta(minutes=(candles_count + 10) * 60)
		end_time = current_time
		recent_candles_list = get_h1_candles(contract_symbol, start_time, end_time)[1][:-1][-candles_count:]
		recent_h1_open_prices_list = [float(candle.open) for candle in recent_candles_list]
		recent_h1_high_prices_list = [float(candle.high) for candle in recent_candles_list]
		recent_h1_low_prices_list = [float(candle.low) for candle in recent_candles_list]
		recent_h1_close_prices_list = [float(candle.close) for candle in recent_candles_list]
	if timeframe == "h2":
		start_time = current_time - timedelta(minutes=(candles_count + 10) * 60 * 2)
		end_time = current_time
		recent_candles_list = get_h2_candles(contract_symbol, start_time, end_time)[1][:-1][-candles_count:]
		recent_h2_open_prices_list = [float(candle.open) for candle in recent_candles_list]
		recent_h2_high_prices_list = [float(candle.high) for candle in recent_candles_list]
		recent_h2_low_prices_list = [float(candle.low) for candle in recent_candles_list]
		recent_h2_close_prices_list = [float(candle.close) for candle in recent_candles_list]
	if timeframe == "h4":
		start_time = current_time - timedelta(minutes=(candles_count + 10) * 60 * 4)
		end_time = current_time
		recent_candles_list = get_h4_candles(contract_symbol, start_time, end_time)[1][:-1][-candles_count:]
		recent_h4_open_prices_list = [float(candle.open) for candle in recent_candles_list]
		recent_h4_high_prices_list = [float(candle.high) for candle in recent_candles_list]
		recent_h4_low_prices_list = [float(candle.low) for candle in recent_candles_list]
		recent_h4_close_prices_list = [float(candle.close) for candle in recent_candles_list]
	if timeframe == "d1":
		start_time = current_time - timedelta(minutes=(candles_count + 10) * 60 * 24)
		end_time = current_time
		recent_candles_list = get_d1_candles(contract_symbol, start_time, end_time)[1][:-1][-candles_count:]
		recent_d1_open_prices_list = [float(candle.open) for candle in recent_candles_list]
		recent_d1_high_prices_list = [float(candle.high) for candle in recent_candles_list]
		recent_d1_low_prices_list = [float(candle.low) for candle in recent_candles_list]
		recent_d1_close_prices_list = [float(candle.close) for candle in recent_candles_list]


def load_indicators_dict() -> None:
	global indicators_dict
	indicators_dict = load_indicators_dict_from_file(INDICATORS_DICT_FILENAME)


def load_indicators_dict_from_file(filename: str = INDICATORS_DICT_FILENAME) -> list:
	global indicators_dict
	with open(filename, 'rb') as handle:
		return pickle.load(handle)


def save_indicators_dict() -> None:
	save_indicators_dict_to_file(INDICATORS_DICT_FILENAME)


def save_indicators_dict_to_file(filename: str = INDICATORS_DICT_FILENAME) -> None:
	global indicators_dict
	with open(filename, 'wb') as handle:
		pickle.dump(indicators_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


def update_indicators_dict(
	contract_symbol: str,
	current_time: datetime, 
	timeframe: str
) -> None:
	global indicators_dict
	if timeframe == "m1":
		candles_list = get_m1_candles(contract_symbol, datetime.fromtimestamp(indicators_dict["candle_close_timestamp"]), current_time)[1]
	if timeframe == "m5":
		candles_list = get_m5_candles(contract_symbol, datetime.fromtimestamp(indicators_dict["candle_close_timestamp"]), current_time)[1]
	if timeframe == "m15":
		candles_list = get_m15_candles(contract_symbol, datetime.fromtimestamp(indicators_dict["candle_close_timestamp"]), current_time)[1]
	if timeframe == "h1":
		candles_list = get_h1_candles(contract_symbol, datetime.fromtimestamp(indicators_dict["candle_close_timestamp"]), current_time)[1]
	close_prices_list = [candle.close for candle in candles_list]
	open_times_list = [candle.open_time for candle in candles_list]
	close_times_list = [candle.close_time for candle in candles_list]
	_ema_50 = indicators_dict["ema_50"]
	_ema_40 = indicators_dict["ema_40"]
	_ema_30 = indicators_dict["ema_30"]
	_ema_20 = indicators_dict["ema_20"]
	_ema_10 = indicators_dict["ema_10"]
	_macd_ema_12 = indicators_dict["macd_ema_12"]
	_macd_ema_26 = indicators_dict["macd_ema_26"]
	_macd_line = indicators_dict["macd_line"]
	_signal_line = indicators_dict["signal_line"]
	len(close_prices_list)
	for i in range(len(close_prices_list)):
		_close_price = round(float(close_prices_list[i]), PRICE_DECIMAL_DIGITS)
		_open_time = open_times_list[i].timestamp()
		_close_time = close_times_list[i].timestamp()
		if timeframe == "m1" and current_time - timedelta(minutes=1) < datetime.fromtimestamp(_open_time):
			break
		if timeframe == "m5" and current_time - timedelta(minutes=5) < datetime.fromtimestamp(_open_time):
			break
		if timeframe == "m15" and current_time - timedelta(minutes=15) < datetime.fromtimestamp(_open_time):
			break
		if timeframe == "h1" and current_time - timedelta(minutes=60) < datetime.fromtimestamp(_open_time):
			break
		_ema_50 = round(get_new_ema(_ema_50, _close_price, 50), INDICATORS_DECIMAL_DIGITS)
		_ema_40 = round(get_new_ema(_ema_40, _close_price, 40), INDICATORS_DECIMAL_DIGITS)
		_ema_30 = round(get_new_ema(_ema_30, _close_price, 30), INDICATORS_DECIMAL_DIGITS)
		_ema_20 = round(get_new_ema(_ema_20, _close_price, 20), INDICATORS_DECIMAL_DIGITS)
		_ema_10 = round(get_new_ema(_ema_10, _close_price, 10), INDICATORS_DECIMAL_DIGITS)
		_macd_ema_12 = round(get_new_ema(_macd_ema_12, _close_price, 12), INDICATORS_DECIMAL_DIGITS)
		_macd_ema_26 = round(get_new_ema(_macd_ema_26, _close_price, 26), INDICATORS_DECIMAL_DIGITS)
		_macd_line = round(_macd_ema_12 - _macd_ema_26, INDICATORS_DECIMAL_DIGITS)
		_signal_line = round(get_new_ema(_signal_line, _macd_line, 9), INDICATORS_DECIMAL_DIGITS)
		indicators_dict = {
			"candle_open_timestamp": _open_time,
			"candle_close_timestamp": _close_time,
			"candle_close_price": _close_price,
			"ema_50": _ema_50,
			"ema_40": _ema_40,
			"ema_30": _ema_30,
			"ema_20": _ema_20,
			"ema_10": _ema_10,
			"macd_ema_12": _macd_ema_12,
			"macd_ema_26": _macd_ema_26,
			"macd_line": _macd_line,
			"signal_line": _signal_line,
		}


def update_account_balance(first_coin_symbol: str) -> int:
	global account_available_balance
	global total_account_balance
	global last_account_available_balances_list
	global last_total_account_balances_list
	last_account_available_balances_list.append(account_available_balance)
	last_total_account_balances_list.append(total_account_balance)
	if len(last_account_available_balances_list) > LAST_ACCOUNT_BALANCES_LIST_MAX_LENGTH:
		last_account_available_balances_list = last_account_available_balances_list[-LAST_ACCOUNT_BALANCES_LIST_MAX_LENGTH:]
	if len(last_total_account_balances_list) > LAST_ACCOUNT_BALANCES_LIST_MAX_LENGTH:
		last_total_account_balances_list = last_total_account_balances_list[-LAST_ACCOUNT_BALANCES_LIST_MAX_LENGTH:]
	for i in range(MAXIMUM_NUMBER_OF_API_CALL_TRIES):
		if True:
			balance_list = binance_spot_api.account()["balances"]
			account_available_balance = 0
			total_account_balance = 0
			for balance_dict in balance_list:
				if balance_dict["asset"] == first_coin_symbol:
					account_available_balance = float(balance_dict["free"])
					total_account_balance = float(balance_dict["free"]) + float(balance_dict["locked"])
			return SUCCESSFUL
		else:
			pass
	logging.error("ERROR in update_account_balance")
	return ERROR


@retry(MAXIMUM_NUMBER_OF_API_CALL_TRIES, lambda e: logging.error(f"ERROR in update_contract_last_price: {e}") or ERROR)
def update_contract_last_price(contract_symbol: str) -> int:
	global contract_last_price
	contract_last_price = float(binance_spot_api.ticker_price(symbol=contract_symbol)["price"])
	return SUCCESSFUL


def init_bot() -> None:
	global binance_spot_api
	binance_spot_api = Spot(api_key=API_KEY, api_secret=SECRET_KEY)


def update_is_price_increasing(
	price_direction_indicator_name_1: str, 
	price_direction_indicator_name_2: str
) -> None:
	global last_is_price_increasing
	global is_price_increasing
	global indicators_dict
	global contract_last_price
	last_is_price_increasing = is_price_increasing
	is_price_increasing = indicators_dict[price_direction_indicator_name_1] > indicators_dict[price_direction_indicator_name_2]


def update_is_price_decreasing(
	price_direction_indicator_name_1: str,
	price_direction_indicator_name_2: str
) -> None:
	global last_is_price_decreasing
	global is_price_decreasing
	global indicators_dict
	global contract_last_price
	last_is_price_decreasing = is_price_decreasing
	is_price_decreasing = indicators_dict[price_direction_indicator_name_1] < indicators_dict[price_direction_indicator_name_2]


def update_is_macd_increasing() -> None:
	global last_is_macd_increasing
	global is_macd_increasing
	global indicators_dict
	last_is_macd_increasing = is_macd_increasing
	is_macd_increasing = indicators_dict["macd_line"] > indicators_dict["signal_line"]


def update_is_macd_decreasing() -> None:
	global last_is_macd_decreasing
	global is_macd_decreasing
	global indicators_dict
	global contract_last_price
	last_is_macd_decreasing = is_macd_decreasing
	is_macd_decreasing = indicators_dict["macd_line"] < indicators_dict["signal_line"]


def update_is_macd_positive() -> None:
	global last_is_macd_positive
	global is_macd_positive
	global indicators_dict
	last_is_macd_positive = is_macd_positive
	is_macd_positive = indicators_dict["macd_line"] > 0


def update_is_macd_negative() -> None:
	global last_is_macd_negative
	global is_macd_negative
	global indicators_dict
	global contract_last_price
	last_is_macd_negative = is_macd_negative
	is_macd_negative = indicators_dict["macd_line"] < 0


def is_oco_active() -> bool:
	return len(binance_spot_api.get_oco_open_orders()) != 0


def is_it_time_to_buy() -> bool:
	return is_bot_started and is_price_increasing and not last_is_price_increasing


def is_it_time_to_update_and_trade(current_time: datetime) -> bool:
	second = int(current_time.second) % 60
	return HANDLING_POSITIONS_TIME_SECOND <= second and second <= HANDLING_POSITIONS_TIME_SECOND + 1


def buy_with_oco(
	contract_symbol: str,
	first_coin_amount: float,
	take_profit_percent: float, 
	stop_loss_percent: float,
) -> int:
	logging.info("=" * 60)
	logging.info("buy")
	market_order_created = False
	position_quantity = round_down(WALLET_USAGE_PERCENT / 100 * first_coin_amount / contract_last_price, POSITION_QUANTITY_DECIMAL_DIGITS)
	if position_quantity < 10 ** (-POSITION_QUANTITY_DECIMAL_DIGITS):
		logging.info("=" * 60)
		return SUCCESSFUL
	for i in range(MAXIMUM_NUMBER_OF_API_CALL_TRIES):
		try:
			update_contract_last_price(contract_symbol)
			market_order = binance_spot_api.new_order(symbol=contract_symbol,
													  side="BUY",
													  quantity=position_quantity,
													  type="MARKET",
													  timestamp=get_local_timestamp())
			send_buy_message()
			market_order_created = True
			break
		except:
			pass
	if not market_order_created:
		logging.error("ERROR in buy")
		logging.info("=" * 60)
		return ERROR
	sleep(4 * SLEEP_INTERVAL)
	for i in range(MAXIMUM_NUMBER_OF_API_CALL_TRIES):
		try:
			position_entry_price = contract_last_price
			market_order = binance_spot_api.get_order(symbol=contract_symbol, orderId=market_order["orderId"], timestamp=get_local_timestamp())
			try:
				if float(market_order["price"]) > 0:
					position_entry_price = contract_last_price
			except:
				pass
			take_profit_price = round((1 + take_profit_percent / 100) * position_entry_price, PRICE_DECIMAL_DIGITS)
			stop_loss_price = round((1 + stop_loss_percent / 100) * position_entry_price, PRICE_DECIMAL_DIGITS)
			oco_order = binance_spot_api.new_oco_order(symbol=contract_symbol,
													   side="SELL",
													   price=take_profit_price,
													   stopPrice=stop_loss_price,
													   stopLimitPrice=stop_loss_price,
													   stopLimitTimeInForce="GTC",
													   quantity=position_quantity,
													   timestamp=get_local_timestamp())
			send_oco_message()
			return SUCCESSFUL
		except:
			pass
	logging.error("ERROR in buy_with_oco")
	logging.info("=" * 60)
	return ERROR


def main() -> None:
	logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s',
						datefmt='%Y/%m/%d %I:%M:%S %p',
						handlers=[logging.FileHandler("application.log"), logging.StreamHandler(sys.stdout)])
	global is_bot_started
	init_bot()
	update_account_balance(FIRST_COIN_SYMBOL)
	while True:
		sleep(SLEEP_INTERVAL)
		update_current_time()
		if not is_it_time_to_update_and_trade(current_time):
			continue
		load_indicators_dict()
		update_indicators_dict(CONTRACT_SYMBOL, current_time, TIMEFRAME)
		update_current_time()
		update_recent_prices_list(CONTRACT_SYMBOL, current_time, IMPORTANT_CANDLES_COUNT, TIMEFRAME)
		save_indicators_dict()
		update_contract_last_price(CONTRACT_SYMBOL)
		update_is_price_increasing(PRICE_DIRECTION_INDICATOR_NAME_1, PRICE_DIRECTION_INDICATOR_NAME_2)
		update_is_price_decreasing(PRICE_DIRECTION_INDICATOR_NAME_1, PRICE_DIRECTION_INDICATOR_NAME_2)
		update_is_macd_increasing()
		update_is_macd_decreasing()
		update_is_macd_positive()
		update_is_macd_negative()
		update_account_balance(FIRST_COIN_SYMBOL)
		log_results()
		sleep(4 * SLEEP_INTERVAL)
		if not is_oco_active() and (True or is_it_time_to_buy()):
				buy_with_oco(CONTRACT_SYMBOL, total_account_balance, TAKE_PROFIT_PERCENT,
							 STOP_LOSS_PERCENT)
		is_bot_started = True


def log_results() -> None:
	output = (
		f"{'_' * 60}\n"
		f"CONTRACT_SYMBOL:{str(CONTRACT_SYMBOL)}\n"
		f"PRICE_DIRECTION_INDICATOR_NAMES:{str(PRICE_DIRECTION_INDICATOR_NAME_1)}{str(PRICE_DIRECTION_INDICATOR_NAME_2)}\n"
		f"current_time:{str(current_time)}\n"
		f"account_available_balance:{str(account_available_balance)}{str(FIRST_COIN_SYMBOL)}\n"
		f"total_account_balance:{str(total_account_balance)}{str(FIRST_COIN_SYMBOL)}\n"
		f"last_account_available_balances_list:{str(last_account_available_balances_list)}\n"
		f"last_total_account_balances_list:{str(last_total_account_balances_list)}\n"
		f"is_price_increasing:{str(is_price_increasing)}\n"
		f"is_price_decreasing:{str(is_price_decreasing)}\n"
		f"is_macd_increasing:{str(is_macd_increasing)}\n"
		f"is_macd_decreasing:{str(is_macd_decreasing)}\n"
		f"is_macd_positive:{str(is_macd_positive)}\n"
		f"is_macd_negative:{str(is_macd_negative)}\n"
		f"indicators_dict:{str(indicators_dict)}\n"
	)

	logging.info(output)
	send_message(output)


if __name__ == "__main__":
	main()
