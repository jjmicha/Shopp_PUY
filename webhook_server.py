# webhook_server.py - полностью переделываем для демо-режима
from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
import time

app = Flask(__name__)

# HTML страница для демо-оплаты
PAYMENT_PAGE_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Демо-оплата | Тинькофф</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container { 
            max-width: 440px; 
            width: 100%;
        }
        .card { 
            background: white; 
            border-radius: 20px; 
            padding: 40px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }
        .bank-header { 
            display: flex; 
            align-items: center; 
            margin-bottom: 30px; 
            justify-content: center;
        }
        .bank-logo { 
            width: 50px; 
            height: 50px; 
            background: #FFDD2D; 
            border-radius: 12px; 
            margin-right: 15px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #333;
        }
        .bank-name { 
            font-size: 24px; 
            font-weight: 700; 
            color: #1a1a1a; 
        }
        .amount { 
            font-size: 42px; 
            font-weight: 800; 
            text-align: center; 
            margin: 30px 0; 
            color: #1a1a1a;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .payment-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 12px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }
        .form-group { 
            margin-bottom: 25px; 
        }
        label { 
            display: block; 
            margin-bottom: 8px; 
            color: #666; 
            font-size: 14px;
            font-weight: 500;
        }
        input { 
            width: 100%; 
            padding: 15px; 
            border: 2px solid #e1e5e9; 
            border-radius: 10px; 
            font-size: 16px; 
            transition: all 0.3s ease;
        }
        input:focus { 
            outline: none; 
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .btn { 
            width: 100%; 
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; 
            border: none; 
            padding: 18px; 
            border-radius: 12px; 
            font-size: 18px; 
            font-weight: 600;
            cursor: pointer; 
            transition: all 0.3s ease;
            margin-top: 10px;
        }
        .btn:hover { 
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        .demo-note { 
            background: #e3f2fd; 
            padding: 15px; 
            border-radius: 12px; 
            margin-top: 25px; 
            font-size: 14px; 
            color: #1565c0;
            border-left: 4px solid #2196f3;
        }
        .card-example {
            background: #fff3cd;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            font-family: monospace;
            border: 1px dashed #ffc107;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="bank-header">
                <div class="bank-logo">Т</div>
                <div class="bank-name">Тинькофф</div>
            </div>

            <div class="amount">{{ amount }} ₽</div>

            <div class="payment-info">
                <strong>Информация о платеже:</strong><br>
                Магазин: Demo Shop<br>
                ID платежа: {{ payment_id }}
            </div>

            <form method="POST">
                <div class="form-group">
                    <label>Номер карты</label>
                    <div class="card-example">2200 0000 0000 4242 - Успешная оплата</div>
                    <input type="text" name="card" placeholder="2200 0000 0000 4242" required>
                </div>

                <div class="form-group">
                    <label>Срок действия</label>
                    <input type="text" name="expiry" placeholder="12/25" value="12/25" required>
                </div>

                <div class="form-group">
                    <label>CVC</label>
                    <input type="text" name="cvc" placeholder="123" value="123" required>
                </div>

                <div class="form-group">
                    <label>Имя держателя карты</label>
                    <input type="text" name="holder" placeholder="IVAN IVANOV" value="DEMO USER" required>
                </div>

                <button type="submit" class="btn">Оплатить {{ amount }} ₽</button>
            </form>

            <div class="demo-note">
                💡 <strong>Демо-режим</strong><br>
                Это тестовая оплата, деньги не списываются.<br>
                Используйте тестовые номера карт для симуляции платежей.
            </div>
        </div>
    </div>
</body>
</html>
'''

SUCCESS_PAGE_HTML = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <title>Оплата успешна</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            background: linear-gradient(135deg, #4CAF50, #45a049);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            margin: 0;
        }
        .success-card {
            background: white;
            padding: 50px;
            border-radius: 20px;
            text-align: center;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            max-width: 500px;
            width: 100%;
        }
        .success-icon {
            font-size: 80px;
            color: #4CAF50;
            margin-bottom: 20px;
        }
        h1 {
            color: #1a1a1a;
            margin-bottom: 20px;
        }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            margin-top: 20px;
            text-decoration: none;
            display: inline-block;
        }
    </style>
</head>
<body>
    <div class="success-card">
        <div class="success-icon">✅</div>
        <h1>Оплата прошла успешно!</h1>
        <p><strong>Сумма:</strong> {{ amount }} руб.</p>
        <p><strong>ID платежа:</strong> {{ payment_id }}</p>
        <p><strong>Карта:</strong> •••• {{ card_last_four }}</p>
        <p>Вернитесь в Telegram бот и нажмите "Проверить оплату"</p>
        <button class="btn" onclick="window.close()">Закрыть окно</button>
    </div>
</body>
</html>
'''


def get_db_connection():
    conn = sqlite3.connect('shop_bot.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/pay/<payment_id>', methods=['GET'])
def payment_page(payment_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM yookassa_payments WHERE payment_id = ?', (payment_id,))
    payment = cursor.fetchone()
    conn.close()

    if not payment:
        return "Платеж не найден", 404

    amount = payment['amount']
    return render_template_string(PAYMENT_PAGE_HTML, amount=amount, payment_id=payment_id)


@app.route('/pay/<payment_id>', methods=['POST'])
def process_payment(payment_id):
    card_number = request.form.get('card', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Обновляем статус платежа на "успешно"
    cursor.execute(
        'UPDATE yookassa_payments SET status = "succeeded" WHERE payment_id = ?',
        (payment_id,)
    )

    # Получаем информацию о платеже
    cursor.execute('SELECT * FROM yookassa_payments WHERE payment_id = ?', (payment_id,))
    payment = cursor.fetchone()

    conn.commit()
    conn.close()

    # Определяем последние 4 цифры карты
    card_last_four = card_number[-4:] if len(card_number) >= 4 else '4242'

    return render_template_string(
        SUCCESS_PAGE_HTML,
        amount=payment['amount'],
        payment_id=payment_id,
        card_last_four=card_last_four
    )


@app.route('/success')
def success_page():
    return '''
    <html>
        <head>
            <title>Оплата успешна</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                .success { color: green; font-size: 24px; }
            </style>
        </head>
        <body>
            <div class="success">✅ Оплата прошла успешно!</div>
            <p>Вернитесь в телеграм бот и нажмите "Проверить оплату"</p>
        </body>
    </html>
    '''


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)