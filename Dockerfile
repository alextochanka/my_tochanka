FROM python:3.10

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код приложения
COPY . .

# Директория для логов
RUN mkdir -p logs

# Запускаем main.py (который запускает Flask и Telegram-бот)
CMD ["python", "main.py"]