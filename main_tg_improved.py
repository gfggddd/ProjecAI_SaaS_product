
import asyncio
from datetime import datetime, timedelta
import config_new as config
from logger_config import logger
from database.sheets import save_booking_async, modify_booking_async
from agents.manager_improved import run_manager_agent
from agents.extractor_improved import run_extractor_agent
from error_handler import handle_error, BotException
from security import RateLimiter, DataValidator, CircuitBreaker
from health_check import health_checker
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart

# Инициализация
bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher()

# Защита и мониторинг
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
circuit_breaker = CircuitBreaker(failure_threshold=5)
USER_SESSIONS = {}
MAX_HISTORY_SIZE = 50

def get_history(user_id: int) -> list:
    """Получает историю чата пользователя."""
    if user_id not in USER_SESSIONS:
        USER_SESSIONS[user_id] = {
            "messages": [],
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
    return USER_SESSIONS[user_id]["messages"]

def add_to_history(user_id: int, role: str, content: str):
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
    
    # Очищаем старую историю если нужно
    if len(session["messages"]) > MAX_HISTORY_SIZE:
        session["messages"] = session["messages"][-MAX_HISTORY_SIZE:]

async def cleanup_old_sessions():
    """Очищает старые сессии (старше 24 часов)."""
    while True:
        try:
            now = datetime.now()
            old_sessions = [
                uid for uid, data in USER_SESSIONS.items()
                if now - data["last_activity"] > timedelta(hours=24)
            ]
            for uid in old_sessions:
                del USER_SESSIONS[uid]
                logger.info(f"Cleaned old session for user {uid}")
            
            await asyncio.sleep(3600)  # Проверяем каждый час
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")

async def notify_admin(name: str, phone: str, date: str, time: str, service: str):
    """Уведомляет администратора о новой записи."""
    text = f"💈 **Новая запись!**\n👤 {name}\n📞 {phone}\n📅 {date}\n⏰ {time}\n✂️ {service}"
    try:
        await bot.send_message(
            chat_id=config.TELEGRAM_ADMIN_ID,
            text=text,
            parse_mode="Markdown"
        )
        logger.info(f"Admin notified about booking: {phone}")
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")
        health_checker.record_error("admin_notification")

async def bg_save_booking(name: str, phone: str, date: str, time: str, service: str, user_id: int):
    """Фоновое сохранение записи."""
    try:
        health_checker.record_request()
        
        if not circuit_breaker.is_available():
            await bot.send_message(
                chat_id=user_id,
                text="⚠️ Система временно перегружена. Попробуйте позже."
            )
            logger.warning("Circuit breaker is open")
            return
        
        result = await save_booking_async(name, phone, date, time, service)
        
        if result == True:
            circuit_breaker.record_success()
            asyncio.create_task(notify_admin(name, phone, date, time, service))
            await bot.send_message(
                chat_id=user_id,
                text="✅ Вы успешно записаны! Ожидаем вас.",
                parse_mode="Markdown"
            )
            logger.info(f"Booking created: {phone}")
        elif result == "BUSY":
            await bot.send_message(
                chat_id=user_id,
                text="❌ Извините, это время уже занято. Пожалуйста, выберите другое."
            )
        else:
            circuit_breaker.record_failure()
            await bot.send_message(
                chat_id=user_id,
                text="❌ Ошибка при сохранении. Попробуйте позже."
            )
            
    except Exception as e:
        logger.error(f"Error in bg_save_booking: {e}")
        health_checker.record_error(f"bg_save_booking: {str(e)}")
        await bot.send_message(
            chat_id=user_id,
            text="❌ Ошибка обработки. Свяжитесь с администратором."
        )

async def bg_modify_booking(phone: str, action: str, new_date: str, new_time: str, user_id: int):
    """Фоновое обновление/отмена записи."""
    try:
        health_checker.record_request()
        
        if not circuit_breaker.is_available():
            await bot.send_message(
                chat_id=user_id,
                text="⚠️ Система временно перегружена. Попробуйте позже."
            )
            return
        
        result = await modify_booking_async(phone, action, new_date, new_time)
        
        if result == True:
            circuit_breaker.record_success()
            action_text = "перенесена" if action == "update" else "отменена"
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ Ваша запись успешно {action_text}!"
            )
            logger.info(f"Booking {action}d: {phone}")
        elif result == "BUSY":
            await bot.send_message(
                chat_id=user_id,
                text="❌ Это время уже занято. Выберите другое."
            )
        else:
            await bot.send_message(
                chat_id=user_id,
                text="❌ Запись не найдена. Проверьте номер телефона."
            )
            
    except Exception as e:
        logger.error(f"Error in bg_modify_booking: {e}")
        health_checker.record_error(f"bg_modify_booking: {str(e)}")

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Команда /start."""
    try:
        user_id = message.from_user.id
        if not rate_limiter.is_allowed(str(user_id)):
            await message.answer("⚠️ Слишком много запросов. Попробуйте позже.")
            return
        
        await message.answer(f"Здравствуйте! Я помогу вам записаться в {config.BUSINESS_NAME}. 📅")
        logger.info(f"User {user_id} started bot")
    except Exception as e:
        logger.error(f"Error in cmd_start: {e}")

@dp.message()
async def telegram_chat_router(message: types.Message):
    """Основной роутер сообщений."""
    try:
        user_id = message.from_user.id
        user_text = message.text
        
        # Проверка rate limiting
        if not rate_limiter.is_allowed(str(user_id)):
            await message.answer("⚠️ Слишком много запросов. Подождите минуту.")
            logger.warning(f"Rate limit exceeded for user {user_id}")
            return
        
        # Валидация входных данных
        try:
            user_text = DataValidator.validate_text(user_text)
        except BotException as e:
            await message.answer(e.user_message)
            return
        
        health_checker.record_request()
        add_to_history(user_id, "user", user_text)
        chat_history = get_history(user_id)
        
        # Получаем ответ от ИИ
        if not circuit_breaker.is_available():
            await message.answer("⚠️ Система перегружена. Попробуйте позже.")
            logger.warning("Circuit breaker is open")
            return
        
        manager_reply = await run_manager_agent(user_text, chat_history)
        add_to_history(user_id, "assistant", manager_reply)
        
        circuit_breaker.record_success()
        
        # Обработка по тегам действий
        if "[ACTION:CREATE]" in manager_reply:
            clean_reply = manager_reply.replace("[ACTION:CREATE]", "").strip()
            await message.answer(clean_reply)
            
            async def extract_and_save():
                try:
                    data = await run_extractor_agent(chat_history)
                    name = data.get("name", "Клиент").strip()
                    phone = data.get("phone", "Не указано").strip()
                    date = data.get("date", "").strip()
                    time = data.get("time", "").strip()
                    service = data.get("service", "").strip()
                    
                    # Валидация
                    if not date or date == "Не указано" or not time or time == "Не указано":
                        await message.answer("⚠️ Укажите дату (ДД.ММ.ГГГГ) и время (ЧЧ:ММ).")
                        return
                    
                    try:
                        name = DataValidator.validate_name(name)
                        phone = DataValidator.validate_phone(phone)
                        date = DataValidator.validate_date(date)
                        time = DataValidator.validate_time(time)
                    except BotException as e:
                        await message.answer(f"❌ {e.user_message}")
                        return
                    
                    await bg_save_booking(name, phone, date, time, service, user_id)
                except Exception as e:
                    logger.error(f"Error in extract_and_save: {e}")
                    health_checker.record_error(f"extract_and_save: {str(e)}")
            
            asyncio.create_task(extract_and_save())
        
        elif "[ACTION:UPDATE]" in manager_reply:
            clean_reply = manager_reply.replace("[ACTION:UPDATE]", "").strip()
            await message.answer(clean_reply)
            
            async def extract_and_update():
                try:
                    data = await run_extractor_agent(chat_history)
                    phone = data.get("phone", "Не указано").strip()
                    date = data.get("date", "").strip()
                    time = data.get("time", "").strip()
                    
                    if phone == "Не указано":
                        await message.answer("⚠️ Укажите номер телефона для поиска записи.")
                        return
                    
                    try:
                        phone = DataValidator.validate_phone(phone)
                        if date:
                            date = DataValidator.validate_date(date)
                        if time:
                            time = DataValidator.validate_time(time)
                    except BotException as e:
                        await message.answer(f"❌ {e.user_message}")
                        return
                    
                    await bg_modify_booking(phone, "update", date, time, user_id)
                except Exception as e:
                    logger.error(f"Error in extract_and_update: {e}")
                    health_checker.record_error(f"extract_and_update: {str(e)}")
            
            asyncio.create_task(extract_and_update())
        
        elif "[ACTION:CANCEL]" in manager_reply:
            clean_reply = manager_reply.replace("[ACTION:CANCEL]", "").strip()
            await message.answer(clean_reply)
            
            async def extract_and_cancel():
                try:
                    data = await run_extractor_agent(chat_history)
                    phone = data.get("phone", "Не указано").strip()
                    
                    if phone == "Не указано":
                        await message.answer("⚠️ Укажите номер телефона.")
                        return
                    
                    try:
                        phone = DataValidator.validate_phone(phone)
                    except BotException as e:
                        await message.answer(f"❌ {e.user_message}")
                        return
                    
                    await bg_modify_booking(phone, "cancel", None, None, user_id)
                except Exception as e:
                    logger.error(f"Error in extract_and_cancel: {e}")
                    health_checker.record_error(f"extract_and_cancel: {str(e)}")
            
            asyncio.create_task(extract_and_cancel())
        
        else:
            await message.answer(manager_reply)
        
        logger.debug(f"Message processed for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error in telegram_chat_router: {e}")
        health_checker.record_error(f"telegram_router: {str(e)}")
        circuit_breaker.record_failure()
        try:
            await message.answer("❌ Ошибка обработки. Попробуйте позже.")
        except:
            pass

async def main():
    """Главная функция."""
    logger.info(f"🚀 Starting Telegram bot for {config.BUSINESS_NAME}")
    
    # Запускаем очищение сессий
    asyncio.create_task(cleanup_old_sessions())
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Telegram bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
