# handlers/admin.py
def setup_admin_handlers(bot):
    @bot.message_handler(commands=['add_product'])
    def add_product(message):
        # Проверка прав администратора
        if message.from_user.id not in ADMIN_IDS:
            return

        # Логика добавления товара
        # ...