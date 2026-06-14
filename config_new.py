"""
Главный файл конфигурации приложения.
Использует переменные окружения из .env файла.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from logger_config import logger

# Загружаем переменные из .env файла
load_dotenv()

# ========== БАЗОВЫЕ НАСТРОЙКИ ==========
BASE_DIR = Path(__file__).resolve().parent
PROJECT_NAME = "COMTEHNO"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

logger.info(f"🚀 Загружен конфиг для окружения: {ENVIRONMENT}")

# ========== ИИ МОДЕЛЬ (DEEPSEEK) ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")

if not DEEPSEEK_API_KEY:
    raise ValueError("❌ DEEPSEEK_API_KEY не установлен в .env файле!")

# ========== ТЕЛЕГРАМ БОТ ==========
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))
ENABLE_TELEGRAM = os.getenv("ENABLE_TELEGRAM", "True").lower() == "true"

if ENABLE_TELEGRAM and not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN не установлен в .env файле!")

# ========== WHATSAPP API ==========
WA_TOKEN = os.getenv("WA_TOKEN", "")
WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID", "")
WA_VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "verify_token_123")
WA_PORT = int(os.getenv("WA_PORT", "8001"))
ENABLE_WHATSAPP = os.getenv("ENABLE_WHATSAPP", "False").lower() == "true"

if ENABLE_WHATSAPP and (not WA_TOKEN or not WA_PHONE_NUMBER_ID):
    logger.warning("⚠️ WhatsApp параметры не полностью установлены. Функции WhatsApp отключены.")
    ENABLE_WHATSAPP = False

# ========== GOOGLE SHEETS ==========
CREDS_PATH = os.getenv("CREDS_PATH", "./creds.json")
SPREADSHEET_NAME = os.getenv("SPREADSHEET_NAME", "BarBershop client")

# Проверяем существование файла учётных данных
if not os.path.exists(CREDS_PATH):
    logger.warning(f"⚠️ Файл учётных данных {CREDS_PATH} не найден. БД операции будут недоступны.")

# ========== ПУТИ К ПАПКАМ ==========
CHROMA_DB_PATH = BASE_DIR / "chroma_db"
BASE_VECTOR_PATH = BASE_DIR / "BASE_VECTOR"
LOGS_PATH = BASE_DIR / "logs"
DATABASE_PATH = BASE_DIR / "database"

# Создаём необходимые папки
for path in [CHROMA_DB_PATH, BASE_VECTOR_PATH, LOGS_PATH]:
    path.mkdir(exist_ok=True)

# ========== RAG СИСТЕМА (CHROMA) ==========
EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PERSIST_DIRECTORY = str(CHROMA_DB_PATH)
VECTOR_DATA_FILE = BASE_VECTOR_PATH / "DATA_AI.txt"

# ========== БИЗНЕС-ЛОГИКА ==========
BUSINESS_NAME = os.getenv("BUSINESS_NAME", "COMTEHO")
BUSINESS_TIMEZONE = os.getenv("BUSINESS_TIMEZONE", "Asia/Bishkek")
BOOKING_BUFFER_MINUTES = int(os.getenv("BOOKING_BUFFER_MINUTES", "30"))

# ========== ЛОГИРОВАНИЕ ==========
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(LOGS_PATH / "app.log"))

# ========== СООБЩЕНИЯ И ШАБЛОНЫ ==========
MESSAGES = {
    "start": f"Здравствуйте! Я помогу вам записаться в {BUSINESS_NAME}. 📅",
    "booking_confirmed": "✅ Вы успешно записаны! Ожидаем вас.",
    "booking_updated": "✅ Ваша запись успешно перенесена!",
    "booking_cancelled": "✅ Ваша запись успешно отменена.",
    "busy": f"❌ Извините, это время уже занято. Выберите другое.",
    "error": "❌ Произошла ошибка. Пожалуйста, попробуйте позже.",
    "missing_data": "⚠️ Укажите дату (ДД.ММ.ГГГГ) и время (ЧЧ:ММ).",
}

# ========== ВАЛИДАЦИЯ КОНФИГА ==========
def validate_config():
    """Проверяет критичные параметры конфига."""
    errors = []
    
    if not DEEPSEEK_API_KEY:
        errors.append("❌ DEEPSEEK_API_KEY отсутствует")
    
    if ENABLE_TELEGRAM and not TELEGRAM_TOKEN:
        errors.append("❌ TELEGRAM_TOKEN отсутствует")
    
    if ENABLE_WHATSAPP and (not WA_TOKEN or not WA_PHONE_NUMBER_ID):
        errors.append("❌ WhatsApp параметры отсутствуют")
    
    if not os.path.exists(CREDS_PATH):
        logger.warning(f"⚠️ Google Sheets учётные данные не найдены в {CREDS_PATH}")
    
    if errors:
        logger.error("Критические ошибки конфига:")
        for error in errors:
            logger.error(error)
        raise RuntimeError("Неполная конфигурация приложения")
    
    logger.info("✅ Конфигурация успешно загружена и валидирована")

# Запускаем валидацию при импорте
try:
    validate_config()
except RuntimeError as e:
    logger.error(f"Ошибка конфигурации: {e}")
    if ENVIRONMENT == "production":
        raise

# ========== ВЫВОД КОНФИГА (для отладки) ==========
if DEBUG:
    logger.debug(f"Проект: {PROJECT_NAME}")
    logger.debug(f"Окружение: {ENVIRONMENT}")
    logger.debug(f"Telegram включен: {ENABLE_TELEGRAM}")
    logger.debug(f"WhatsApp включен: {ENABLE_WHATSAPP}")
    logger.debug(f"Бизнес: {BUSINESS_NAME}")
    logger.debug(f"Папка логов: {LOGS_PATH}")
