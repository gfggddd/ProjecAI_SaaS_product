import logging
import os
from pathlib import Path

def setup_logger(name: str = "app", level: str = "INFO"):
    """
    Централизованная конфигурация логирования для всего приложения.
    
    Аргументы:
        name: Имя логгера
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Возвращает:
        logger: Настроенный объект логгера
    """
    # Создаём папку для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Получаем уровень логирования из переменной окружения или параметра
    log_level = os.getenv("LOG_LEVEL", level).upper()
    log_file = os.getenv("LOG_FILE", str(log_dir / "app.log"))
    
    # Создаём логгер
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level))
    
    # Проверяем, чтобы не добавлять handlers дважды
    if logger.hasHandlers():
        return logger
    
    # Форматер логов
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для файла
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(getattr(logging, log_level))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Главный логгер приложения
logger = setup_logger("BOT-APP")
