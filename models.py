import sqlite3
from datetime import datetime


class Database:
    def __init__(self, db_path='shop_bot.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация таблиц БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Пользователи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE NOT NULL,
                username VARCHAR(32),
                balance DECIMAL(10,2) DEFAULT 0.00,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_blocked BOOLEAN DEFAULT FALSE
            )
        ''')

        # Товары
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                description TEXT,
                file_id VARCHAR(255),
                external_url VARCHAR(255),
                available_count INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Платежи
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                currency VARCHAR(3) DEFAULT 'RUB',
                provider VARCHAR(20) NOT NULL,
                provider_payment_id VARCHAR(255),
                status VARCHAR(20) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Покупки
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                status VARCHAR(20) DEFAULT 'completed',
                delivered_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        ''')

        # Тикеты
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'open',
                admin_reply TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Возвраты
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS refunds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                purchase_id INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                amount DECIMAL(10,2) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (purchase_id) REFERENCES purchases(id)
            )
        ''')

        # Создаем индексы для ускорения запросов
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_purchases_user_id ON purchases(user_id)')

        conn.commit()
        conn.close()

    def get_connection(self):
        """Получить соединение с БД"""
        return sqlite3.connect(self.db_path)

    def add_user(self, telegram_id, username):
        """Добавить пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO users (telegram_id, username) 
                VALUES (?, ?)
            ''', (telegram_id, username))
            conn.commit()
        finally:
            conn.close()

    def get_user(self, telegram_id):
        """Получить пользователя"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def get_products(self):
        """Получить все товары"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM products WHERE available_count > 0')
            return cursor.fetchall()
        finally:
            conn.close()

    def get_product(self, product_id):
        """Получить товар по ID"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
            return cursor.fetchone()
        finally:
            conn.close()

    def add_purchase(self, user_id, product_id, price):
        """Добавить покупку"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO purchases (user_id, product_id, price) 
                VALUES (?, ?, ?)
            ''', (user_id, product_id, price))

            # Уменьшаем количество доступного товара
            cursor.execute('''
                UPDATE products SET available_count = available_count - 1 
                WHERE id = ?
            ''', (product_id,))

            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()