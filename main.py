from multiprocessing import Process
import app
import telegram_bot

# Запуск всех приложений
def run_flask():
    print("Старт Flask app...")
    try:
        if app.initialize_database():
            app.app.run(host="0.0.0.0")
        else:
            print("База данных не инициализирована!")
    except Exception as e:
        print(f"Flask error: {e}")

def run_telegram_bot():
    print("Старт Telegram bot...")
    try:
        telegram_bot.start_bot()
    except Exception as e:
        print(f"Ошибка телеграм-бота: {e}")

if __name__ == '__main__':
    print("Старт Football App and Telegram Bot...")

    flask_process = Process(target=run_flask)
    telegram_process = Process(target=run_telegram_bot)

    flask_process.start()
    telegram_process.start()

    try:
        flask_process.join()
        telegram_process.join()
    except KeyboardInterrupt:
        print("\nПрерывание.")
        flask_process.terminate()
        telegram_process.terminate()
        flask_process.join()
        telegram_process.join()
        print("Все процессы остановлены.")

