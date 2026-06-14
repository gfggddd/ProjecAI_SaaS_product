"""
Улучшенный WhatsApp бот с защитой и валидацией.
SaaS-ready версия.
"""
import asyncio
from datetime import datetime, timedelta
import config_new as config
from logger_config import logger
import aiohttp
from fastapi import FastAPI, Request, Response, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import uvicorn

from database.sheets import save_booking_async, modify_booking_async
from agents.manager_improved import run_manager_agent
from agents.extractor_improved import run_extractor_agent
from error_handler import BotException
from security import RateLimiter, DataValidator, CircuitBreaker
from health_check import health_checker

# Инициализация
app = FastAPI(
    title="BarberBot AI WhatsApp",
    version="1.0.0",
    docs_url="/docs" if config.DEBUG else None
)

# Middleware безопасности
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # В production ограничить!
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Защита и мониторинг
rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
circuit_breaker = CircuitBreaker(failure_threshold=5)
USER_SESSIONS = {}
MAX_HISTORY_SIZE = 50
HTTP_TIMEOUT = aiohttp.ClientTimeout(total=30)

def get_history(user_id: str) -> list:
    """Получает историю чата."""
    if user_id not in USER_SESSIONS:
        USER_SESSIONS[user_id] = {
            "messages": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
    return USER_SESSIONS[user_id]["messages"]

def add_to_history(user_id: str, role: str, content: str):
    """Добавляет сообщение в историю."""
    if user_id not in USER_SESSIONS:
        USER_SESSIONS[user_id] = {
            "messages": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
    
    session = USER_SESSIONS[user_id]
    session["messages"].append({"role": role, "content": content})
    session["last_activity"] = datetime.now()
    
    if len(session["messages"]) > MAX_HISTORY_SIZE:
        session["messages"] = session["messages"][-MAX_HISTORY_SIZE:]

async def send_whatsapp_message(to_phone: str, text: str, retries: int = 3) -> bool:
    """Отправляет сообщение в WhatsApp с retry logic."""
    url = f"https://graph.facebook.com/v17.0/{config.WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text[:4096]}  # Max length limit
    }
    
    for attempt in range(retries):
        try:
            async with aiohttp.ClientSession(timeout=HTTP_TIMEOUT) as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"WhatsApp message sent to {to_phone}")
                        return True
                    else:
                        error = await response.text()
                        logger.warning(f"WhatsApp API error: {error}")
                        if attempt < retries - 1:
                            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            logger.error(f"WhatsApp send error (attempt {attempt + 1}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
    
    circuit_breaker.record_failure()
    return False

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return await health_checker.check_all()

@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    """Верификация вебхука от Meta."""
    if mode == "subscribe" and token == config.WA_VERIFY_TOKEN:
        logger.info("✅ WhatsApp webhook verified")
        return Response(content=challenge, media_type="text/plain")
    
    logger.warning("❌ Invalid webhook verification attempt")
    return Response(content="Invalid token", status_code=403)

@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    """Прием сообщений от WhatsApp."""
    try:
        # Получаем JSON
        data = await request.json()
        
        # Валидация структуры
        if not isinstance(data, dict) or "entry" not in data:
            logger.warning("Invalid webhook payload structure")
            return {"status": "ok"}
        
        # Парсинг сообщения
        try:
            message_obj = data["entry"][0]["changes"][0]["value"]["messages"][0]
            wa_id = message_obj["from"].strip()
            user_text = message_obj.get("text", {}).get("body", "").strip()
        except (KeyError, IndexError, TypeError) as e:
            logger.warning(f"Failed to parse WhatsApp message: {e}")
            return {"status": "ok"}
        
        # Проверка rate limiting
        if not rate_limiter.is_allowed(wa_id):
            await send_whatsapp_message(wa_id, "⚠️ Слишком много запросов. Попробуйте позже.")
            logger.warning(f"Rate limit exceeded for {wa_id}")
            return {"status": "ok"}
        
        # Валидация текста
        try:
            user_text = DataValidator.validate_text(user_text)
        except BotException:
            await send_whatsapp_message(wa_id, "❌ Сообщение слишком длинное или пусто.")
            return {"status": "ok"}
        
        health_checker.record_request()
        
        # Проверка circuit breaker
        if not circuit_breaker.is_available():
            await send_whatsapp_message(wa_id, "⚠️ Система перегружена. Попробуйте позже.")
            logger.warning("Circuit breaker is open")
            return {"status": "ok"}
        
        # Обработка сообщения
        add_to_history(wa_id, "user", user_text)
        chat_history = get_history(wa_id)
        
        manager_reply = await run_manager_agent(user_text, chat_history)
        add_to_history(wa_id, "assistant", manager_reply)
        
        circuit_breaker.record_success()
        
        # Отправляем ответ
        await send_whatsapp_message(wa_id, manager_reply)
        
        # Обработка действий (триггеры)
        triggers = ["записал", "оформил", "заявка принята", "подтверждаю", "отменил", "перенес", "обновил"]
        if any(tg in manager_reply.lower() for tg in triggers):
            logger.debug(f"Action trigger detected for {wa_id}")
            
            async def process_action():
                try:
                    extracted = await run_extractor_agent(chat_history)
                    
                    action = extracted.get("action", "create")
                    name = extracted.get("name", "Клиент").strip()
                    phone = extracted.get("phone", wa_id).strip()
                    date = extracted.get("date", "").strip()
                    time = extracted.get("time", "").strip()
                    service = extracted.get("service", "").strip()
                    
                    # Валидация
                    if action == "create":
                        try:
                            name = DataValidator.validate_name(name)
                            phone = DataValidator.validate_phone(phone)
                            date = DataValidator.validate_date(date)
                            time = DataValidator.validate_time(time)
                        except BotException as e:
                            await send_whatsapp_message(wa_id, f"❌ {e.user_message}")
                            return
                        
                        result = await save_booking_async(name, phone, date, time, service)
                        if result == True:
                            await send_whatsapp_message(wa_id, "✅ Вы успешно записаны!")
                            logger.info(f"Booking created: {phone}")
                        elif result == "BUSY":
                            await send_whatsapp_message(wa_id, "❌ Это время занято. Выберите другое.")
                    
                    elif action in ["update", "cancel"]:
                        try:
                            phone = DataValidator.validate_phone(phone)
                            if date:
                                date = DataValidator.validate_date(date)
                            if time:
                                time = DataValidator.validate_time(time)
                        except BotException as e:
                            await send_whatsapp_message(wa_id, f"❌ {e.user_message}")
                            return
                        
                        result = await modify_booking_async(phone, action, date, time)
                        if result == True:
                            action_text = "перенесена" if action == "update" else "отменена"
                            await send_whatsapp_message(wa_id, f"✅ Запись успешно {action_text}!")
                
                except Exception as e:
                    logger.error(f"Error processing action: {e}")
                    health_checker.record_error(f"process_action: {str(e)}")
            
            asyncio.create_task(process_action())
        
        logger.debug(f"Message processed for {wa_id}")
        
    except Exception as e:
        logger.error(f"Error in receive_whatsapp_message: {e}")
        health_checker.record_error(f"whatsapp_router: {str(e)}")
        circuit_breaker.record_failure()
    
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    """Метрики для мониторинга."""
    health = await health_checker.check_all()
    return {
        "health": health,
        "rate_limiter_users": len(rate_limiter.requests),
        "sessions": len(USER_SESSIONS),
        "circuit_breaker_open": circuit_breaker.is_open
    }

if __name__ == "__main__":
    logger.info(f"🚀 Starting WhatsApp bot for {config.BUSINESS_NAME}")
    uvicorn.run(
        "main_wa_improved:app",
        host="0.0.0.0",
        port=config.WA_PORT,
        reload=False,
        access_log=True
    )
