#!/usr/bin/env python3
"""
Утилита для быстрого создания новой конфигурации бизнеса.
Копирует проект и адаптирует под новый тип бизнеса.

Использование:
    python duplicate_for_business.py --name "My Salon" --type beauty --folder ~/my-salon-bot
"""
import os
import shutil
from pathlib import Path
import argparse
import json
from datetime import datetime

BUSINESS_TYPES = {
    "barbershop": "Барбершоп",
    "beauty": "Салон красоты",
    "gym": "Фитнес-центр",
    "clinic": "Клиника",
    "restaurant": "Ресторан",
    "hotel": "Отель",
    "education": "Учебное заведение",
}

BUSINESS_TEMPLATES = {
    "barbershop": """НАЗВАНИЕ БИЗНЕСА: {name}
КОНТАКТЫ: 
  Телефон: +996 555 XX-XX-XX
  Адрес: Город, ул. Название, №XX
  Instagram: @username

УСЛУГИ И ЦЕНЫ:
  1. Стрижка классическая - 250 сом (30 мин)
  2. Стрижка с бородой - 350 сом (45 мин)
  3. Королевское бритьё - 200 сом (20 мин)

МАСТЕРА:
  МАСТЕР: Имя. РАНГ: Главный мастер.
  МАСТЕР: Имя2. РАНГ: Мастер.

ГРАФИК РАБОТЫ:
  Пн-Пт: 10:00 - 20:00
  Сб-Вс: 11:00 - 18:00
""",
    "beauty": """НАЗВАНИЕ БИЗНЕСА: {name}
КОНТАКТЫ:
  Телефон: +996 555 XX-XX-XX
  Адрес: Город, ул. Название
  Instagram: @username

УСЛУГИ И ЦЕНЫ:
  1. Маникюр - 400 сом (45 мин)
  2. Педикюр - 500 сом (60 мин)
  3. Наращивание ресниц - 800 сом (90 мин)
  4. Брови - 200 сом (30 мин)

СПЕЦИАЛИСТЫ:
  СПЕЦИАЛИСТ: Имя. СПЕЦИАЛЬНОСТЬ: Маникюр/педикюр
  СПЕЦИАЛИСТ: Имя2. СПЕЦИАЛЬНОСТЬ: Ресницы

ГРАФИК РАБОТЫ:
  Пн-Пт: 09:00 - 20:00
  Сб: 10:00 - 18:00
  Вс: выходной
""",
    "gym": """НАЗВАНИЕ БИЗНЕСА: {name}
КОНТАКТЫ:
  Телефон: +996 555 XX-XX-XX
  Адрес: Город, ул. Название
  Website: www.example.com

УСЛУГИ И ЦЕНЫ:
  1. Персональная тренировка - 500 сом (60 мин)
  2. Групповой класс - 200 сом (45 мин)
  3. Абонемент месячный - 5000 сом
  4. Консультация тренера - 300 сом (30 мин)

ТРЕНЕРЫ:
  ТРЕНЕР: Имя. СПЕЦИАЛЬНОСТЬ: Силовой тренинг
  ТРЕНЕР: Имя2. СПЕЦИАЛЬНОСТЬ: Йога

ГРАФИК РАБОТЫ:
  Пн-Пт: 06:00 - 23:00
  Сб-Вс: 08:00 - 22:00
""",
    "clinic": """НАЗВАНИЕ БИЗНЕСА: {name}
КОНТАКТЫ:
  Телефон: +996 555 XX-XX-XX
  Адрес: Город, ул. Название
  Email: contact@example.com

ВРАЧИ И УСЛУГИ:
  ВРАЧ: Имя. СПЕЦИАЛЬНОСТЬ: Терапевт. ОПЫТ: XX лет
  ВРАЧ: Имя2. СПЕЦИАЛЬНОСТЬ: Кардиолог. ОПЫТ: XX лет

УСЛУГИ:
  1. Первичный приём - 500 сом (30 мин)
  2. Повторный приём - 400 сом (20 мин)
  3. УЗИ диагностика - 800 сом (30 мин)
  4. Анализы - от 100 сом

ГРАФИК РАБОТЫ:
  Пн-Пт: 09:00 - 18:00
  Сб: 09:00 - 14:00
  Вс: выходной
""",
}

def create_business_directory(business_name: str, business_type: str, target_folder: str):
    """Создаёт новую папку для бизнеса с адаптированной конфигурацией."""
    
    print(f"✅ Создание проекта для: {business_name} ({BUSINESS_TYPES.get(business_type, 'Unknown')})")
    
    target_path = Path(target_folder)
    
    # Проверка существования папки
    if target_path.exists():
        print(f"⚠️  Папка {target_folder} уже существует!")
        response = input("Перезаписать? (y/n): ")
        if response.lower() != 'y':
            return
        shutil.rmtree(target_path)
    
    # Копирование основных файлов
    print("📋 Копирование файлов...")
    target_path.mkdir(parents=True)
    
    files_to_copy = [
        "main_tg.py", "main_wa.py", "run_all.py",
        "agents/", "database/",
        "requirements_clean.txt", "init_project.py",
        "config_new.py", "logger_config.py",
        "error_handler.py", "constants.py",
        ".gitignore", "Dockerfile", "docker-compose.yml"
    ]
    
    for file in files_to_copy:
        src = Path(__file__).parent / file
        dst = target_path / file
        
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
    
    # Создание документации
    print("📚 Создание документации...")
    
    readme_content = f"""# {business_name} - AI Booking Bot

Автоматизированная система записей на основе ИИ.

## Быстрый старт

1. Установите зависимости: `pip install -r requirements_clean.txt`
2. Инициализируйте проект: `python init_project.py`
3. Отредактируйте `.env` с вашими данными
4. Запустите: `python main_tg.py` (или `main_wa.py`)

## Документация

- [SETUP.md](SETUP.md) - Детальная инструкция установки
- [README.md](README.md) - Полная документация

## Конфигурация

Основные параметры в `.env`:
- DEEPSEEK_API_KEY - ИИ модель
- TELEGRAM_TOKEN - Telegram бот
- BUSINESS_NAME - Название ({business_name})
- BUSINESS_TIMEZONE - Часовой пояс

Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(target_path / "BUSINESS_README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    # Создание адаптированного .env.example
    print("⚙️  Создание конфигурации...")
    
    env_content = f"""# {business_name} - Конфигурация

# ИИ МОДЕЛЬ
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
LLM_MODEL=deepseek-chat

# TELEGRAM БОТ
TELEGRAM_TOKEN=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
TELEGRAM_ADMIN_ID=123456789

# WHATSAPP API
WA_TOKEN=your_whatsapp_token
WA_PHONE_NUMBER_ID=your_phone_id
WA_VERIFY_TOKEN=verify_token_123
WA_PORT=8001

# GOOGLE SHEETS
CREDS_PATH=./creds.json
SPREADSHEET_NAME={business_name} Bookings

# ЛОГИРОВАНИЕ
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# ОКРУЖЕНИЕ
ENVIRONMENT=development
DEBUG=True

# БИЗНЕС-ЛОГИКА
BUSINESS_NAME={business_name}
BUSINESS_TIMEZONE=Asia/Bishkek
BOOKING_BUFFER_MINUTES=30
ENABLE_TELEGRAM=True
ENABLE_WHATSAPP=False
"""
    
    with open(target_path / ".env.example", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    # Создание адаптированного шаблона бизнеса
    print("🏢 Создание шаблона бизнеса...")
    
    template_content = BUSINESS_TEMPLATES.get(business_type, BUSINESS_TEMPLATES["barbershop"])
    template_content = template_content.format(name=business_name)
    
    base_vector_path = target_path / "BASE_VECTOR"
    base_vector_path.mkdir(exist_ok=True)
    
    with open(base_vector_path / "business_data.txt", "w", encoding="utf-8") as f:
        f.write(template_content)
    
    # Создание папок
    for folder in ["logs", "chroma_db", "database"]:
        (target_path / folder).mkdir(exist_ok=True)
    
    # Метаданные проекта
    print("📝 Сохранение метаданных...")
    
    metadata = {
        "name": business_name,
        "type": business_type,
        "type_display": BUSINESS_TYPES.get(business_type, "Unknown"),
        "created": datetime.now().isoformat(),
        "version": "1.0.0"
    }
    
    with open(target_path / "business_config.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"""
✅ Проект успешно создан!

📁 Папка: {target_folder}
🏢 Бизнес: {business_name}
📊 Тип: {BUSINESS_TYPES.get(business_type, 'Unknown')}

Следующие шаги:
1. cd {target_folder}
2. python init_project.py
3. Отредактируйте .env.example → .env с вашими ключами API
4. Отредактируйте BASE_VECTOR/business_data.txt с информацией о вашем бизнесе
5. python main_tg.py (или python run_all.py)

Полная документация: SETUP.md и README.md
    """)

def main():
    parser = argparse.ArgumentParser(
        description="Создайте новый проект для вашего бизнеса"
    )
    parser.add_argument("--name", required=True, help="Название бизнеса")
    parser.add_argument(
        "--type",
        default="barbershop",
        choices=list(BUSINESS_TYPES.keys()),
        help="Тип бизнеса"
    )
    parser.add_argument("--folder", default=None, help="Папка для проекта (по умолчанию: ./{name}-bot)")
    
    args = parser.parse_args()
    
    # Определяем папку по умолчанию
    folder = args.folder or f"./{args.name.lower().replace(' ', '-')}-bot"
    
    create_business_directory(args.name, args.type, folder)

if __name__ == "__main__":
    main()
