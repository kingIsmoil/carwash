# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем зависимости для сборки пакетов Python
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Сначала копируем только файл зависимостей
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Копируем весь проект
COPY . .

# Открываем порт
EXPOSE 8000

# Запуск (но в docker-compose будет свой command)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
