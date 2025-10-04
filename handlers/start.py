import telebot
from models import Database

db = Database()


def setup_start_handlers(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        # Добавляем пользователя в БД
        user_id = message.from_user.id
        username = message.from_user.username

        db.add_user(user_id, username)

        # Создаем клавиатуру
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton('🛍️ Каталог товаров')
        btn2 = telebot.types.KeyboardButton('💰 Мой баланс')
        btn3 = telebot.types.KeyboardButton('📦 Мои покупки')
        btn4 = telebot.types.KeyboardButton('🆘 Поддержка')
        markup.add(btn1, btn2, btn3, btn4)

        bot.send_message(
            message.chat.id,
            'Привет! 👋 Я магазин пресетов и гайдов.\n\n'
            'Выбери действие ниже:',
            reply_markup=markup
        )

    @bot.message_handler(func=lambda message: message.text == '🛍️ Каталог товаров')
    def show_catalog(message):
        products = db.get_products()

        if not products:
            bot.send_message(message.chat.id, '📭 В магазине пока нет товаров')
            return

        for product in products:
            product_id, name, price, description, file_id, external_url, available_count, created_at = product

            text = f'''
🛒 {name}
💵 Цена: {price} руб.
📝 {description}
📦 В наличии: {available_count} шт.
'''
            markup = telebot.types.InlineKeyboardMarkup()
            buy_btn = telebot.types.InlineKeyboardButton(
                'Купить',
                callback_data=f'buy_{product_id}'
            )
            markup.add(buy_btn)

            if file_id:
                # Если есть файл (пресет), отправляем его
                bot.send_document(
                    message.chat.id,
                    file_id,
                    caption=text,
                    reply_markup=markup
                )
            else:
                # Если это гайд (ссылка)
                bot.send_message(
                    message.chat.id,
                    text,
                    reply_markup=markup
                )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def handle_buy(call):
        product_id = int(call.data.split('_')[1])
        product = db.get_product(product_id)
        user = db.get_user(call.from_user.id)

        if not product:
            bot.answer_callback_query(call.id, 'Товар не найден')
            return

        if product[6] <= 0:  # available_count
            bot.answer_callback_query(call.id, 'Товар закончился')
            return

        # Здесь будет логика покупки
        # Пока просто создаем запись о покупке
        purchase_id = db.add_purchase(user[0], product_id, product[2])

        bot.answer_callback_query(call.id, '✅ Покупка успешна!')
        bot.send_message(
            call.message.chat.id,
            f'✅ Вы успешно приобрели: {product[1]}\n'
            f'💵 Стоимость: {product[2]} руб.\n'
            f'📦 Номер заказа: #{purchase_id}'
        )