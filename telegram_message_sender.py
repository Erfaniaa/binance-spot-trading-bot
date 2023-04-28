import telegram
from credentials import TELEGRAM_API_KEY, TELEGRAM_USER_ID
from config import SEND_TELEGRAM_MESSAGE
import logging


if SEND_TELEGRAM_MESSAGE:
    telegram_bot = telegram.Bot(token=TELEGRAM_API_KEY)


def send_buy_message():
    send_message("buy")


def send_sell_message():
    send_message("sell")


def send_oco_message():
    send_message("oco")


def send_message(message):
    if not SEND_TELEGRAM_MESSAGE:
        return

    try:
        telegram_bot.send_message(chat_id=TELEGRAM_USER_ID, text=message)
    except telegram.error.TelegramError:
        logging.error("ERROR in sending message to telegram")
