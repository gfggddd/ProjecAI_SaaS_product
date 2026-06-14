#!/usr/bin/env python3
"""
Скрипт инициализации проекта.
Выполняет первичную настройку, проверку зависимостей и создание необходимых папок.
"""
import os
import sys
from pathlib import Path
from shutil import copy
import subprocess

def print_header(text):
    """Красивый вывод заголовков."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    """Зелёный успех."""
    print(f"✅ {text}")

def print_error(text):
    """Красная ошибка."""
    print(f"❌ {text}")
    sys.exit(1)

def print_warning(text):
    """Жёлтое предупреждение."""
    print(f"⚠️  {text}")

def check_python_version():
    """Проверяет версию Python."""
    print_header("Проверка версии Python")
    
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print_error(f"Python 3.9+ требуется. Установлена {python_version.major}.{python_version.minor}")
    
    print_success(f"Python {python_version.major}.{python_version.minor}.{python_version.micro} OK")

def setup_env_file():
    """Создаёт .env файл из .env.example если его нет."""
    print_header("Настройка .env файла")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        print_warning(".env файл уже существует. Пропускаем копирование.")
        return
    
    if not env_example.exists():
        print_error(".env.example не найден!")
    
    copy(env_example, env_file)
    print_success(f".env создан из {env_example}")
    print_warning("⚠️ ВАЖНО: Отредактируйте .env файл с вашими реальными данными!")

def create_directories():
    """Создаёт необходимые папки."""
    print_header("Создание директорий")
    
    directories = [
        "logs",
        "chroma_db",
        "BASE_VECTOR",
        "database",
    ]
    
    for directory in directories:
        path = Path(directory)
        path.mkdir(exist_ok=True)
        print_success(f"Папка {directory}/ готова")

def check_dependencies():
    """Проверяет установленные зависимости."""
    print_header("Проверка зависимостей")
    
    try:
        import aiogram
        import openai
        import chromadb
        import gspread
        import fastapi
        print_success("Все критичные зависимости установлены")
    except ImportError as e:
        print_error(f"Отсутствует зависимость: {e}")

def check_credentials():
    """Проверяет наличие файлов учётных данных."""
    print_header("Проверка учётных данных")
    
    creds_file = Path("creds.json")
    
    if creds_file.exists():
        print_success("creds.json найден")
    else:
        print_warning("creds.json не найден. Google Sheets API не будет работать.")
        print("  1. Создайте OAuth 2.0 сервис-аккаунт в Google Cloud Console")
        print("  2. Скачайте JSON ключ и сохраните как creds.json")
        print("  3. Предоставьте доступ сервис-аккаунту к вашей Google Sheet")

def check_vector_data():
    """Проверяет наличие файла с данными для RAG."""
    print_header("Проверка данных для RAG системы")
    
    vector_file = Path("BASE_VECTOR/barber_data.txt")
    
    if vector_file.exists():
        print_success(f"Файл {vector_file} найден")
        with open(vector_file) as f:
            lines = len(f.readlines())
        print(f"  Содержит {lines} строк")
    else:
        print_warning(f"Файл {vector_file} не найден. Создайте его с информацией о вашем бизнесе.")

def show_next_steps():
    """Показывает следующие шаги."""
    print_header("📋 Следующие шаги")
    
    print("""
1. Отредактируйте .env файл:
   - Установите DEEPSEEK_API_KEY
   - Установите TELEGRAM_TOKEN и ADMIN_ID
   - Установите другие параметры (WhatsApp, Google Sheets и т.д.)

2. Создайте файлы учётных данных:
   - creds.json для Google Sheets (если используется)

3. Добавьте данные о вашем бизнесе:
   - Отредактируйте BASE_VECTOR/barber_data.txt
   - Или измените constants.py для другого типа бизнеса

4. Запустите бота:
   - Для Telegram: python main_tg.py
   - Для WhatsApp: python main_wa.py

5. (Опционально) Запустите оба одновременно:
   - python run_all.py
    """)

def main():
    """Главная функция."""
    print_header("🚀 Инициализация проекта")
    
    check_python_version()
    create_directories()
    setup_env_file()
    check_dependencies()
    check_credentials()
    check_vector_data()
    show_next_steps()
    
    print_header("✨ Инициализация завершена!")
    print("""
Для вопросов и помощи смотрите README.md и SETUP.md
    """)

if __name__ == "__main__":
    main()
