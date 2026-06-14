import config
import asyncio
import re
from database.sheets import save_booking_async, modify_booking_async
from agents.manager import run_manager_agent
from agents.extractor import run_extractor_agent
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart

bot = Bot(token=config.TELEGRAM_TOKEN)
dp = Dispatcher()

USER_SESSIONS = {}

def get_history(user_id: int) -> list:
    if user_id not in USER_SESSIONS: USER_SESSIONS[user_id] = []
    return USER_SESSIONS[user_id]

def add_to_history(user_id: int, role: str, content: str):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > 20: USER_SESSIONS[user_id] = history[-20:]

# Фоновая функция: уведомление админу
async def notify_admin(name, phone, date, time, service):
    text = f"💈 **Новая запись!**\n👤 {name}\n📞 {phone}\n📅 {date}\n⏰ {time}\n✂️ {service}"
    try:
        await bot.send_message(chat_id=config.ADMIN_ID, text=text, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ Ошибка уведомления: {e}")

# Фоновая функция: сохранение записи
async def bg_save_booking(name, phone, date, time, service, user_id):
    result = await save_booking_async(name, phone, date, time, service)
    
    if result == True:
        asyncio.create_task(notify_admin(name, phone, date, time, service))
        await bot.send_message(chat_id=user_id, text="✅ Вы успешно записаны!")
    elif result == "BUSY":
        await bot.send_message(chat_id=user_id, text="❌ Извините, это время уже занято. Пожалуйста, выберите другое.")
    else:
        await bot.send_message(chat_id=user_id, text="❌ Произошла ошибка при сохранении в базу.")

# Фоновая функция: обновление/отмена записи
async def bg_modify_booking(phone, action, new_date, new_time, user_id):
    result = await modify_booking_async(phone, action, new_date, new_time)
    
    if result == True:
        action_text = "перенесена" if action == "update" else "отменена"
        await bot.send_message(chat_id=user_id, text=f"✅ Ваша запись успешно {action_text}!")
    elif result == "BUSY":
        await bot.send_message(chat_id=user_id, text="❌ Извините, это время уже занято. Выберите другое.")
    else:
        await bot.send_message(chat_id=user_id, text="❌ Записи не найдены или произошла ошибка.")

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("Здравствуйте! Я помогу вам записаться в барбершоп.")

@dp.message()
async def telegram_chat_router(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text
    
    add_to_history(user_id, "user", user_text)
    chat_history = get_history(user_id)

    # 1. Получаем ответ от ИИ (только это в критичном пути)
    manager_reply = await run_manager_agent(user_text, chat_history)
    add_to_history(user_id, "assistant", manager_reply)

    # 2. Обработка по тегам действий (всё остальное в фоне)
    if "[ACTION:CREATE]" in manager_reply:
        # Сразу отправляем ответ клиенту (без тега)
        clean_reply = manager_reply.replace("[ACTION:CREATE]", "").strip()
        await message.answer(clean_reply)
        
        # Фоновая экстракция и сохранение (не блокируем клиента)
        async def extract_and_save():
            data = await run_extractor_agent(chat_history)
            name = data.get("name", "Клиент")
            phone = data.get("phone", "Не указано")
            date = data.get("date")
            time = data.get("time")
            service = data.get("service")
            
            if not date or date == "Не указано" or not time or time == "Не указано":
                await message.answer("⚠️ Укажите дату (ДД.ММ.ГГГГ) и время (ЧЧ:ММ).")
                return
            
            await bg_save_booking(name, phone, date, time, service, user_id)
        
        # Запускаем в фоне - не ждем ответа
        asyncio.create_task(extract_and_save())
        
    elif "[ACTION:UPDATE]" in manager_reply:
        # Сразу отправляем ответ клиенту
        clean_reply = manager_reply.replace("[ACTION:UPDATE]", "").strip()
        await message.answer(clean_reply)
        
        # Фоновое обновление записи
        async def extract_and_update():
            data = await run_extractor_agent(chat_history)
            phone = data.get("phone", "Не указано")
            date = data.get("date")
            time = data.get("time")
            
            if phone == "Не указано":
                await message.answer("⚠️ Не могу найти вашу запись. Укажите номер телефона.")
                return
            
            await bg_modify_booking(phone, "update", date, time, user_id)
        
        asyncio.create_task(extract_and_update())
        
    elif "[ACTION:CANCEL]" in manager_reply:
        # Сразу отправляем ответ клиенту
        clean_reply = manager_reply.replace("[ACTION:CANCEL]", "").strip()
        await message.answer(clean_reply)
        
        # Фоновая отмена записи
        async def extract_and_cancel():
            data = await run_extractor_agent(chat_history)
            phone = data.get("phone", "Не указано")
            
            if phone == "Не указано":
                await message.answer("⚠️ Не могу найти вашу запись. Укажите номер телефона.")
                return
            
            await bg_modify_booking(phone, "cancel", None, None, user_id)
        
        asyncio.create_task(extract_and_cancel())
        
    else:
        # Обычный диалог - просто ответ
        await message.answer(manager_reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())