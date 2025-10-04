import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN', '7529316371:AAEgjrjqwx4rUlH6xdON9AVG_mX3Q4V8RxU')
ADMIN_IDS = [123456789]  # Замените на ваш ID
DATABASE_PATH = 'shop_bot.db'