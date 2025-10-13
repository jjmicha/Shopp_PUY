import telebot


def setup_start_handlers(bot, db):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        username = message.from_user.username

        db.add_user(user_id, username)

        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = telebot.types.KeyboardButton('🛍️ Каталог товаров')
        btn2 = telebot.types.KeyboardButton('📦 Мои покупки')
        markup.add(btn1, btn2)  # Только 2 кнопки теперь

        bot.send_message(
            message.chat.id,
            'Привет! 👋 Я магазин пресетов и гайдов.\n\n'
            '💡 *Режим демо-оплат*\n'
            'Все платежи тестовые, деньги не списываются\n\n'
            'Выбери действие ниже:',
            reply_markup=markup,
            parse_mode='Markdown'
        )

    @bot.message_handler(func=lambda message: message.text == '🛍️ Каталог товаров')
    def show_catalog(message):
        products = db.get_products()

        if not products:
            bot.send_message(message.chat.id, '📭 В магазине пока нет товаров')
            return

        bot.send_message(
            message.chat.id,
            f'🛍️ *В каталоге {len(products)} товаров:*\n'
            f'💡 Все платежи в демо-режиме',
            parse_mode='Markdown'
        )

        for product in products:
            product_id, name, price, description, file_id, external_url, available_count, created_at = product

            text = f'''
🛒 *{name}*
💵 Цена: *{price} руб.*
📝 {description}
📦 В наличии: *{available_count} шт.*
🆔 ID: #{product_id}
'''

            markup = telebot.types.InlineKeyboardMarkup()
            buy_btn = telebot.types.InlineKeyboardButton(
                '🛒 Купить (демо)',
                callback_data=f'buy_{product_id}'
            )
            markup.add(buy_btn)

            bot.send_message(
                message.chat.id,
                text,
                reply_markup=markup,
                parse_mode='Markdown'
            )

