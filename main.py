import telebot
from config import BOT_TOKEN
from models import Database
from handlers.start import setup_start_handlers

# Инициализация бота и БД
bot = telebot.TeleBot(BOT_TOKEN)
db = Database()

# Настройка обработчиков
setup_start_handlers(bot)

if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling(none_stop=True)