# handlers/admin_handlers.py
import telebot
from config import ADMIN_IDS
from models import Database


class AdminStates:
    WAITING_PRODUCT_NAME = 1
    WAITING_PRODUCT_PRICE = 2
    WAITING_PRODUCT_DESCRIPTION = 3
    WAITING_PRODUCT_FILE = 4
    WAITING_PRODUCT_COUNT = 5


def setup_admin_handlers(bot, db):
    admin_states = {}

    def is_admin(user_id):
        return user_id in ADMIN_IDS

    @bot.message_handler(commands=['add_product'])
    def start_add_product(message):
        if not is_admin(message.from_user.id):
            bot.reply_to(message, "⛔ У вас нет прав для выполнения этой команды")
            return

        admin_states[message.from_user.id] = {'state': AdminStates.WAITING_PRODUCT_NAME}
        bot.send_message(message.chat.id, "📝 Введите название товара:")

    @bot.message_handler(func=lambda message:
    message.from_user.id in admin_states and
    admin_states[message.from_user.id]['state'] == AdminStates.WAITING_PRODUCT_NAME)
    def handle_product_name(message):
        admin_states[message.from_user.id].update({
            'state': AdminStates.WAITING_PRODUCT_PRICE,
            'name': message.text
        })
        bot.send_message(message.chat.id, "💰 Введите цену товара (только число):")

    @bot.message_handler(func=lambda message:
    message.from_user.id in admin_states and
    admin_states[message.from_user.id]['state'] == AdminStates.WAITING_PRODUCT_PRICE)
    def handle_product_price(message):
        try:
            price = float(message.text)
            admin_states[message.from_user.id].update({
                'state': AdminStates.WAITING_PRODUCT_DESCRIPTION,
                'price': price
            })
            bot.send_message(message.chat.id, "📄 Введите описание товара:")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Цена должна быть числом. Введите цену еще раз:")

    @bot.message_handler(func=lambda message:
    message.from_user.id in admin_states and
    admin_states[message.from_user.id]['state'] == AdminStates.WAITING_PRODUCT_DESCRIPTION)
    def handle_product_description(message):
        admin_states[message.from_user.id].update({
            'state': AdminStates.WAITING_PRODUCT_COUNT,
            'description': message.text
        })
        bot.send_message(message.chat.id, "📦 Введите количество товара (по умолчанию 1):")

    @bot.message_handler(func=lambda message:
    message.from_user.id in admin_states and
    admin_states[message.from_user.id]['state'] == AdminStates.WAITING_PRODUCT_COUNT)
    def handle_product_count(message):
        try:
            count = int(message.text) if message.text.strip() else 1
            admin_states[message.from_user.id].update({
                'state': AdminStates.WAITING_PRODUCT_FILE,
                'available_count': count
            })
            bot.send_message(message.chat.id, "📎 Теперь отправьте файл для товара (документ, изображение и т.д.):")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Количество должно быть числом. Введите количество еще раз:")

    @bot.message_handler(content_types=['document', 'photo'], func=lambda message:
    message.from_user.id in admin_states and
    admin_states[message.from_user.id]['state'] == AdminStates.WAITING_PRODUCT_FILE)
    def handle_product_file(message):
        user_data = admin_states[message.from_user.id]

        if message.content_type == 'document':
            file_id = message.document.file_id
        elif message.content_type == 'photo':
            file_id = message.photo[-1].file_id  # Берем самое качественное фото
        else:
            bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте файл или изображение")
            return

        try:
            # Добавляем товар в базу данных
            product_id = db.add_product(
                name=user_data['name'],
                price=user_data['price'],
                description=user_data['description'],
                file_id=file_id,
                available_count=user_data.get('available_count', 1)
            )

            # Очищаем состояние
            del admin_states[message.from_user.id]

            bot.send_message(
                message.chat.id,
                f"✅ Товар успешно добавлен!\n"
                f"ID: {product_id}\n"
                f"Название: {user_data['name']}\n"
                f"Цена: {user_data['price']} руб.\n"
                f"Количество: {user_data.get('available_count', 1)} шт."
            )

        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Ошибка при добавлении товара: {str(e)}")
            del admin_states[message.from_user.id]

    @bot.message_handler(commands=['cancel'])
    def cancel_operation(message):
        if message.from_user.id in admin_states:
            del admin_states[message.from_user.id]
            bot.send_message(message.chat.id, "❌ Операция отменена")

    @bot.message_handler(commands=['admin'])
    def admin_panel(message):
        if not is_admin(message.from_user.id):
            return

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton('/add_product')
        btn2 = telebot.types.KeyboardButton('/stats')
        btn3 = telebot.types.KeyboardButton('/cancel')
        markup.add(btn1, btn2, btn3)

        bot.send_message(
            message.chat.id,
            "👨‍💼 Панель администратора\n"
            "Выберите действие:",
            reply_markup=markup
        )