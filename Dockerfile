FROM python:3.10-slim

# Установить рабочую директорию
WORKDIR /app

# Установить системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Скопировать requirements
COPY requirements_clean.txt .

# Установить Python зависимости
RUN pip install --no-cache-dir -r requirements_clean.txt

# Скопировать весь проект
COPY . .

# Создать необходимые папки
RUN mkdir -p logs chroma_db BASE_VECTOR

# Установить переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Использовать по умолчанию config_new вместо config
ENV PYTHONPATH=/app

# Запустить инициализацию и затем приложение
CMD ["sh", "-c", "python init_project.py && python run_all.py"]
