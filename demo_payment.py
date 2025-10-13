# handlers/demo_payment.py
import uuid
import telebot
from config import DEMO_CARDS

# Будет установлено из main.py
DEMO_PAYMENT_URL = None


def setup_demo_payment_handlers(bot, db):
    @bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
    def handle_buy(call):
        if not DEMO_PAYMENT_URL:
            bot.answer_callback_query(call.id, '❌ Платежная система не настроена')
            return

        product_id = int(call.data.split('_')[1])
        product = db.get_product(product_id)
        user = db.get_user(call.from_user.id)

        if not product:
            bot.answer_callback_query(call.id, '❌ Товар не найден')
            return

        if product[6] <= 0:  # available_count
            bot.answer_callback_query(call.id, '❌ Товар закончился')
            return

        # Создаем демо-платеж
        payment_id = str(uuid.uuid4())
        amount = float(product[2])

        try:
            # Сохраняем платеж в БД
            db.create_demo_payment(payment_id, user[0], product_id, amount)

            # Ссылка на демо-страницу оплаты
            payment_url = f"{DEMO_PAYMENT_URL}/pay/{payment_id}"

            # Создаем кнопки (на Replit всегда HTTPS)
            markup = telebot.types.InlineKeyboardMarkup()
            pay_btn = telebot.types.InlineKeyboardButton(
                '💳 Перейти к оплате',
                url=payment_url
            )
            check_btn = telebot.types.InlineKeyboardButton(
                '✅ Проверить оплату',
                callback_data=f'check_{payment_id}'
            )
            markup.add(pay_btn)
            markup.add(check_btn)

            bot.send_message(
                call.message.chat.id,
                f'💳 *Оплата товара*\n\n'
                f'🛒 *{product[1]}*\n'
                f'💵 *Сумма: {amount} руб.*\n'
                f'🆔 *ID платежа: {payment_id}*\n\n'
                f'💡 *Демо-режим:* Используйте тестовую карту:\n`{DEMO_CARDS["success"]}`\n\n'
                f'1. Нажмите "Перейти к оплате"\n'
                f'2. Завершите оплату на странице\n'
                f'3. Вернитесь и нажмите "Проверить оплату"',
                reply_markup=markup,
                parse_mode='Markdown'
            )

            bot.answer_callback_query(call.id, '✅ Ссылка для оплаты отправлена')

        except Exception as e:
            print(f"Payment error: {e}")
            bot.answer_callback_query(call.id, '❌ Ошибка при создании платежа')

    # Остальной код без изменений (check_payment и show_my_purchases)
    @bot.callback_query_handler(func=lambda call: call.data.startswith('check_'))
    def check_payment(call):
        payment_id = call.data.replace('check_', '')
        payment_record = db.get_demo_payment(payment_id)

        if not payment_record:
            bot.answer_callback_query(call.id, '❌ Платеж не найден')
            return

        status = payment_record[4]

        if status == 'succeeded':
            product = db.get_product(payment_record[3])
            user_id = payment_record[2]

            # Создаем запись о покупке
            purchase_id = db.add_purchase(user_id, payment_record[3], payment_record[4])

            # Отправляем файл
            if product[4]:
                try:
                    bot.send_document(
                        call.message.chat.id,
                        product[4],
                        caption=f'✅ *Покупка успешна!*\n\n'
                                f'🛒 *{product[1]}*\n'
                                f'💵 Сумма: {product[2]} руб.\n'
                                f'📦 Номер заказа: #{purchase_id}\n'
                                f'🆔 Платеж: {payment_id}\n\n'
                                f'💡 *Демо-режим:* Деньги не списывались\n\n'
                                f'Спасибо за покупку! 🎉',
                        parse_mode='Markdown'
                    )
                except:
                    bot.send_message(
                        call.message.chat.id,
                        f'✅ *Покупка успешна!*\n\n'
                        f'🛒 *{product[1]}*\n'
                        f'💵 Сумма: {product[2]} руб.\n'
                        f'📦 Номер заказа: #{purchase_id}\n'
                        f'🆔 Платеж: {payment_id}\n\n'
                        f'💡 *Демо-режим:* Деньги не списывались\n\n'
                        f'Спасибо за покупку! 🎉',
                        parse_mode='Markdown'
                    )
            else:
                bot.send_message(
                    call.message.chat.id,
                    f'✅ *Покупка успешна!*\n\n'
                    f'🛒 *{product[1]}*\n'
                    f'💵 Сумма: {product[2]} руб.\n'
                    f'📦 Номер заказа: #{purchase_id}\n'
                    f'🆔 Платеж: {payment_id}\n\n'
                    f'💡 *Демо-режим:* Деньги не списывались\n\n'
                    f'Спасибо за покупку! 🎉',
                    parse_mode='Markdown'
                )

            bot.answer_callback_query(call.id, '✅ Платеж подтвержден')

        elif status == 'pending':
            bot.answer_callback_query(call.id, '⏳ Платеж еще не завершен')
        else:
            bot.answer_callback_query(call.id, '❌ Платеж не найден или отменен')

    @bot.message_handler(func=lambda message: message.text == '📦 Мои покупки')
    def show_my_purchases(message):
        user = db.get_user(message.from_user.id)
        if not user:
            bot.send_message(message.chat.id, '❌ Пользователь не найден')
            return

        purchases = db.get_user_purchases(user[0])

        if not purchases:
            bot.send_message(message.chat.id, '📭 У вас еще нет покупок')
            return

        bot.send_message(message.chat.id, '🛒 *Ваши покупки:*', parse_mode='Markdown')

        for purchase in purchases:
            purchase_id, user_id, product_id, price, status, delivered_at, created_at, product_name, file_id = purchase

            if file_id:
                try:
                    bot.send_document(
                        message.chat.id,
                        file_id,
                        caption=f'🛒 *{product_name}*\n'
                                f'💵 Цена: {price} руб.\n'
                                f'📅 Дата: {created_at}\n'
                                f'📦 Заказ: #{purchase_id}\n\n'
                                f'💡 *Демо-покупка*'
                    )
                except:
                    bot.send_message(
                        message.chat.id,
                        f'🛒 *{product_name}*\n'
                        f'💵 Цена: {price} руб.\n'
                        f'📅 Дата: {created_at}\n'
                        f'📦 Заказ: #{purchase_id}\n\n'
                        f'💡 *Демо-покупка*'
                    )
            else:
                bot.send_message(
                    message.chat.id,
                    f'🛒 *{product_name}*\n'
                    f'💵 Цена: {price} руб.\n'
                    f'📅 Дата: {created_at}\n'
                    f'📦 Заказ: #{purchase_id}\n\n'
                    f'💡 *Демо-покупка*'
                )