"""
Централизованная обработка ошибок и исключений.
Используется для логирования и безопасного сообщения клиентам.
"""
from logger_config import logger
from constants import ERROR_CODES

class BotException(Exception):
    """Базовый класс для исключений бота."""
    
    def __init__(self, message: str, error_code: str = None, user_message: str = None):
        self.message = message
        self.error_code = error_code
        self.user_message = user_message or "❌ Произошла ошибка. Пожалуйста, попробуйте позже."
        super().__init__(self.message)
        
        logger.error(f"[{error_code}] {message}")

class BookingBusyError(BotException):
    """Время уже занято."""
    
    def __init__(self):
        super().__init__(
            message="Запрошенное время уже занято",
            error_code="BUSY",
            user_message="❌ Извините, это время уже занято. Пожалуйста, выберите другое."
        )

class InvalidDataError(BotException):
    """Неверные данные."""
    
    def __init__(self, field: str):
        super().__init__(
            message=f"Неверные данные в поле: {field}",
            error_code="INVALID_DATA",
            user_message=f"⚠️ Ошибка в поле '{field}'. Пожалуйста, проверьте данные."
        )

class BookingNotFoundError(BotException):
    """Запись не найдена."""
    
    def __init__(self):
        super().__init__(
            message="Запись клиента не найдена",
            error_code="NOT_FOUND",
            user_message="❌ Не удалось найти вашу запись. Проверьте номер телефона."
        )

class ExternalAPIError(BotException):
    """Ошибка внешнего API (DeepSeek, Google Sheets и т.д.)."""
    
    def __init__(self, service: str, details: str = ""):
        super().__init__(
            message=f"Ошибка {service} API: {details}",
            error_code="EXTERNAL_API_ERROR",
            user_message="⚠️ Временная ошибка соединения. Пожалуйста, попробуйте позже."
        )

class DatabaseError(BotException):
    """Ошибка базы данных."""
    
    def __init__(self, operation: str, details: str = ""):
        super().__init__(
            message=f"Ошибка БД при операции '{operation}': {details}",
            error_code="DB_ERROR",
            user_message="❌ Ошибка сохранения данных. Попробуйте позже."
        )

class ConfigError(Exception):
    """Ошибка конфигурации."""
    
    def __init__(self, message: str):
        logger.critical(f"❌ Ошибка конфигурации: {message}")
        super().__init__(message)

def handle_error(error: Exception, context: str = "") -> str:
    """
    Обработчик ошибок.
    
    Аргументы:
        error: Исключение
        context: Контекст ошибки (для логирования)
    
    Возвращает:
        user_message: Сообщение для отправки клиенту
    """
    
    if isinstance(error, BotException):
        return error.user_message
    
    elif isinstance(error, TimeoutError):
        logger.error(f"[TIMEOUT] {context}: Таймаут запроса")
        return "⏱️ Запрос занял слишком долго. Попробуйте позже."
    
    elif isinstance(error, ConnectionError):
        logger.error(f"[CONNECTION] {context}: Ошибка соединения")
        return "🌐 Проблема с интернетом. Проверьте соединение."
    
    elif isinstance(error, ValueError):
        logger.error(f"[VALUE_ERROR] {context}: {error}")
        return "⚠️ Ошибка в данных. Пожалуйста, проверьте ввод."
    
    else:
        logger.error(f"[UNEXPECTED] {context}: {type(error).__name__}: {error}")
        return "❌ Неизвестная ошибка. Свяжитесь с администратором."

async def safe_async_operation(
    operation,
    context: str = "",
    fallback_message: str = "❌ Ошибка. Попробуйте позже."
):
    """
    Безопасное выполнение асинхронной операции с обработкой ошибок.
    
    Аргументы:
        operation: Асинхронная функция для выполнения
        context: Контекст операции
        fallback_message: Сообщение при ошибке
    
    Возвращает:
        Результат операции или None при ошибке
    """
    try:
        return await operation()
    except BotException:
        raise
    except Exception as e:
        logger.error(f"[{context}] Ошибка: {e}")
        return None
