"""
Утилиты безопасности и валидации для SaaS приложения.
"""
import re
from datetime import datetime
from typing import Optional
from error_handler import InvalidDataError
from logger_config import logger

class RateLimiter:
    """Rate limiter для защиты от spam."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, user_id: str) -> bool:
        """Проверяет, может ли пользователь отправить запрос."""
        now = datetime.now().timestamp()
        
        if user_id not in self.requests:
            self.requests[user_id] = []
        
        # Очищаем старые запросы
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if now - req_time < self.window_seconds
        ]
        
        # Проверяем лимит
        if len(self.requests[user_id]) >= self.max_requests:
            logger.warning(f"⚠️ Rate limit exceeded for user {user_id}")
            return False
        
        # Добавляем новый запрос
        self.requests[user_id].append(now)
        return True

class DataValidator:
    """Валидирует и санитизирует входные данные."""
    
    # Максимальные длины
    MAX_TEXT_LENGTH = 1000
    MAX_NAME_LENGTH = 100
    MAX_PHONE_LENGTH = 20
    
    # Регулярные выражения
    PHONE_PATTERN = r'^\+?[\d\s\(\)\-]{5,20}$'
    DATE_PATTERN = r'^\d{2}\.\d{2}\.\d{4}$'
    TIME_PATTERN = r'^\d{2}:\d{2}$'
    
    @staticmethod
    def validate_text(text: str, max_length: int = None) -> str:
        """Валидирует и санитизирует текст."""
        if not isinstance(text, str):
            raise InvalidDataError("text")
        
        max_length = max_length or DataValidator.MAX_TEXT_LENGTH
        text = text.strip()
        
        if not text:
            raise InvalidDataError("text (пусто)")
        
        if len(text) > max_length:
            raise InvalidDataError(f"text (> {max_length} символов)")
        
        # Удаляем опасные символы (но оставляем кириллицу и спецсимволы)
        text = re.sub(r'[<>\"\'%;()&+]', '', text)
        
        return text
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Валидирует номер телефона."""
        if not isinstance(phone, str):
            raise InvalidDataError("phone")
        
        phone = phone.strip()
        
        if len(phone) > DataValidator.MAX_PHONE_LENGTH:
            raise InvalidDataError("phone (слишком длинный)")
        
        if not re.match(DataValidator.PHONE_PATTERN, phone):
            raise InvalidDataError("phone (неверный формат)")
        
        return phone
    
    @staticmethod
    def validate_date(date_str: str) -> str:
        """Валидирует дату в формате ДД.ММ.ГГГГ."""
        if not isinstance(date_str, str):
            raise InvalidDataError("date")
        
        date_str = date_str.strip()
        
        if not re.match(DataValidator.DATE_PATTERN, date_str):
            raise InvalidDataError("date (неверный формат, используйте ДД.ММ.ГГГГ)")
        
        try:
            day, month, year = map(int, date_str.split('.'))
            datetime(year, month, day)  # Проверяем корректность даты
        except ValueError:
            raise InvalidDataError("date (невалидная дата)")
        
        # Проверяем что дата не в прошлом
        if datetime(year, month, day).date() < datetime.now().date():
            raise InvalidDataError("date (дата в прошлом)")
        
        return date_str
    
    @staticmethod
    def validate_time(time_str: str) -> str:
        """Валидирует время в формате ЧЧ:ММ."""
        if not isinstance(time_str, str):
            raise InvalidDataError("time")
        
        time_str = time_str.strip()
        
        if not re.match(DataValidator.TIME_PATTERN, time_str):
            raise InvalidDataError("time (неверный формат, используйте ЧЧ:ММ)")
        
        try:
            hour, minute = map(int, time_str.split(':'))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError
        except ValueError:
            raise InvalidDataError("time (невалидное время)")
        
        return time_str
    
    @staticmethod
    def validate_name(name: str) -> str:
        """Валидирует имя."""
        if not isinstance(name, str):
            raise InvalidDataError("name")
        
        name = name.strip()
        
        if not name:
            raise InvalidDataError("name (пусто)")
        
        if len(name) > DataValidator.MAX_NAME_LENGTH:
            raise InvalidDataError(f"name (> {DataValidator.MAX_NAME_LENGTH} символов)")
        
        # Должны быть буквы (кириллица или латиница)
        if not re.match(r'^[а-яёА-ЯЁa-zA-Z\s\-\.]+$', name):
            raise InvalidDataError("name (недопустимые символы)")
        
        return name

class CircuitBreaker:
    """Circuit breaker для защиты от cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failures = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        """Регистрирует успешный запрос."""
        self.failures = 0
        self.is_open = False
    
    def record_failure(self):
        """Регистрирует ошибку."""
        self.failures += 1
        self.last_failure_time = datetime.now().timestamp()
        
        if self.failures >= self.failure_threshold:
            self.is_open = True
            logger.error(f"❌ Circuit breaker OPEN: {self.failures} failures")
    
    def is_available(self) -> bool:
        """Проверяет доступность сервиса."""
        if not self.is_open:
            return True
        
        # Проверяем timeout
        now = datetime.now().timestamp()
        if now - self.last_failure_time > self.timeout_seconds:
            logger.info("🔧 Circuit breaker HALF-OPEN")
            self.is_open = False
            self.failures = 0
            return True
        
        return False
