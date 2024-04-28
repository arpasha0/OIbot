import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests

# Токен вашего бота Telegram
TOKEN = "7129675956:AAHl8R0-5gHsW2DxEDtDznTQuqcMkUusrsE"

# Настройка журналирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение списка доступных криптовалютных фьючерсов на Binance Futures
def get_available_symbols() -> list:
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    response = requests.get(url)
    data = response.json()
    symbols = [symbol["symbol"] for symbol in data["symbols"] if symbol["contractType"] == "PERPETUAL"]
    return symbols

# Получение данных об открытом интересе для указанного символа на Binance Futures
def get_open_interest(symbol: str) -> dict:
    url = "https://fapi.binance.com/futures/data/openInterestHist"
    params = {"symbol": symbol}
    response = requests.get(url, params=params)
    data = response.json()
    return data

# Поиск роста открытого интереса за указанное время
def find_interest_growth(symbol: str, minutes: int, growth_threshold: float) -> bool:
    current_time = datetime.utcnow()
    start_time = current_time - timedelta(minutes=minutes)
    
    open_interest_data = get_open_interest(symbol)
    if "code" in open_interest_data:
        logger.error(f"Ошибка при получении данных об открытом интересе для {symbol}.")
        return False
    
    relevant_entries = [entry for entry in open_interest_data if datetime.utcfromtimestamp(entry["timestamp"]) >= start_time]
    if len(relevant_entries) < 2:
        logger.warning(f"Недостаточно данных для анализа роста открытого интереса для {symbol}.")
        return False
    
    start_interest = relevant_entries[0]["sumOpenInterest"]
    end_interest = relevant_entries[-1]["sumOpenInterest"]
    interest_growth = (end_interest - start_interest) / start_interest * 100
    
    if interest_growth >= growth_threshold:
        return True
    else:
        return False

# Обработчик команды /start
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Привет! Я бот для отслеживания роста открытого интереса криптовалютных фьючерсов на Binance Futures. Используйте команду /scan_interest для сканирования роста.")

# Обработчик команды /scan_interest
def scan_interest(update: Update, context: CallbackContext) -> None:
    growth_threshold = float(context.args[0]) if context.args and context.args[0].isdigit() else 10
    minutes = int(context.args[1]) if context.args and context.args[1].isdigit() else 5
    
    symbols = get_available_symbols()
    message = f"Рост открытого интереса за последние {minutes} минут(у):"
    
    for symbol in symbols:
        if find_interest_growth(symbol, minutes, growth_threshold):
            message += f"\n{symbol}"
    
    update.message.reply_text(message)

# Главная функция
def main() -> None:
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Добавление обработчиков команд
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("scan_interest", scan_interest))

    # Запуск бота
    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
