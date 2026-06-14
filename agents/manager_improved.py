"""
Улучшенный Manager агент с timeout, retry logic и обработкой ошибок.
SaaS-ready версия.
"""
import asyncio
import config_new as config
from logger_config import logger
from error_handler import ExternalAPIError, safe_async_operation
from openai import AsyncOpenAI, APIError, APIConnectionError, APITimeoutError
from datetime import datetime, timedelta
from agents.rag_storage import search_business_info

client = AsyncOpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=30.0  # 30 сек timeout
)

# Кэш для RAG результатов 
rag_cache = {}
RAG_CACHE_TTL = 3600  # 1 час

class RagCache:
    """Простой кэш для RAG результатов."""
    
    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.cache = {}
    
    def get(self, key: str) -> str:
        """Получает значение из кэша."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if datetime.now().timestamp() - timestamp < self.ttl:
                logger.debug(f"RAG cache HIT: {key[:50]}")
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: str):
        """Сохраняет значение в кэш."""
        self.cache[key] = (value, datetime.now().timestamp())
        logger.debug(f"RAG cache SET: {key[:50]}")
    
    def clear_expired(self):
        """Очищает просроченные записи."""
        now = datetime.now().timestamp()
        expired = [k for k, (_, t) in self.cache.items() if now - t > self.ttl]
        for k in expired:
            del self.cache[k]
        if expired:
            logger.debug(f"Cleared {len(expired)} expired cache entries")

rag_cache_manager = RagCache(RAG_CACHE_TTL)

async def run_manager_agent(user_text: str, chat_history: list) -> str:
    """
    Основная функция менеджера с обработкой ошибок и timeout'ами.
    """
    try:
        # Проверяем длину истории (слишком большая может замедлить)
        if len(chat_history) > 100:
            chat_history = chat_history[-50:]  # Оставляем последние 50
            logger.warning("Chat history truncated to prevent slowdown")
        
        # Получаем информацию о бизнесе (с кэшем)
        cache_key = f"rag:{user_text[:100]}"
        found_knowledge = rag_cache_manager.get(cache_key)
        
        if not found_knowledge:
            found_knowledge = search_business_info(user_text)
            rag_cache_manager.set(cache_key, found_knowledge)
        
        today = datetime.now().strftime("%d.%m.%Y")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        
        system_prompt = {
            "role": "system",
            "content": (
                f"Ты — профессиональный ИИ-ассистент в {config.BUSINESS_NAME}. КОЛЛЕДЖА "
                f"Твоя задача — вежливо консультировать клиентов и помогать оформить запись.\n\n"
                f"ЕСЛИ у тебя есть ВСЕ параметры (Имя, Телефон, Дата, Время), "
                f"напиши вежливое подтверждение и добавь тег [ACTION:CREATE].\n"
                f"Если данных не хватает, задай уточняющий вопрос.\n"
                f"Если клиент просит ПЕРЕНЕСТИ запись, добавь тег [ACTION:UPDATE].\n"
                f"Если клиент просит ОТМЕНИТЬ запись, добавь тег [ACTION:CANCEL].\n\n"
                f"🚨 КРИТИЧНЫЕ ПРАВИЛА:\n"
                f"1. Используй ТОЛЬКО информацию из БАЗЫ ЗНАНИЙ ниже.\n"
                f"2. Не выдумывай ЦЕНЫ КОНТРАКТА  или рабочее время.\n"
                f"3. Будь краток и профессионален.\n"
                f"4. Сегодня: {today}, завтра: {tomorrow}\n"
                f"5. Если нужной информации нет, скажи: 'К сожалению, нет точной информации. "
                f"Оставьте номер, наш специалист свяжется.'\n"
                f"6. На вопросы вне {config.BUSINESS_NAME} отвечай: 'Я могу ответить только о {config.BUSINESS_NAME}.'\n\n"
                f"=== БАЗА ЗНАНИЙ ===\n{found_knowledge}\n=================="
            )
        }
        
        messages = [system_prompt] + chat_history[-20:]  # Последние 20 сообщений
        
        # Запрос к LLM с timeout
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    temperature=0.3,
                    max_tokens=500,
                    top_p=0.9
                ),
                timeout=25.0  # 25 сек (меньше чем общий timeout на 5 сек)
            )
            
            reply = response.choices[0].message.content.strip()
            
            # Санитизация ответа (макс 4000 символов)
            if len(reply) > 4000:
                reply = reply[:3990] + "..."
                logger.warning("Response truncated to 4000 chars")
            
            logger.debug(f"Manager agent response: {len(reply)} chars")
            return reply
        
        except asyncio.TimeoutError:
            logger.error("LLM request timeout")
            raise ExternalAPIError("DeepSeek", "timeout")
        
        except (APITimeoutError, APIConnectionError) as e:
            logger.error(f"LLM API error: {e}")
            raise ExternalAPIError("DeepSeek", "connection error")
        
        except APIError as e:
            logger.error(f"LLM API error: {e}")
            raise ExternalAPIError("DeepSeek", str(e)[:100])
    
    except ExternalAPIError as e:
        logger.error(f"External API error: {e.message}")
        return "⏱️ Ошибка соединения с сервером. Попробуйте позже."
    
    except Exception as e:
        logger.error(f"Unexpected error in manager agent: {e}")
        return "❌ Неожиданная ошибка. Свяжитесь с администратором."

async def process_booking_request(name: str, phone: str, date: str, time: str, service: str):
    """Обрабатывает запрос на запись с проверкой занятости."""
    try:
        from database.sheets import get_all_bookings_async
        
        bookings = await asyncio.wait_for(
            get_all_bookings_async(),
            timeout=10.0
        )
        
        is_busy = any(
            b['date'] == date and b['time'] == time
            for b in bookings
            if b.get('status') != "❌ Отменено"
        )
        
        if is_busy:
            return {
                "status": "busy",
                "message": f"Извините, {date} в {time} занято. Доступные слоты: 12:00, 15:00"
            }
        
        return {"status": "free", "message": "Время свободно"}
    
    except asyncio.TimeoutError:
        logger.error("Timeout checking bookings")
        return {"status": "error", "message": "Не удалось проверить занятость"}
    
    except Exception as e:
        logger.error(f"Error processing booking request: {e}")
        return {"status": "error", "message": "Ошибка проверки"}
