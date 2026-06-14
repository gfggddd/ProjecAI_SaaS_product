import config
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from openai import AsyncOpenAI
from datetime import datetime
# Импортируем функции
from agents.rag_storage import search_business_info 
from database.sheets import (
    get_all_bookings_async, 
    save_booking_async, 
    modify_booking_async
)

client = AsyncOpenAI(api_key=config.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

# 1. Отдельная функция для проверки занятости
async def process_booking_request(name, phone, date, time, service):
    bookings = await get_all_bookings_async()
    is_busy = any(b['date'] == date and b['time'] == time for b in bookings)
    
    if is_busy:
        return {
            "status": "busy", 
            "message": f"Извините, на {date} в {time} уже есть запись. Есть свободные слоты на 12:30. Записать вас?"
        }
    
    success = await save_booking_async(name, phone, date, time, service)
    return {"status": "success" if success else "error"}

# 2. Основная функция общения с ИИ
async def run_manager_agent(user_text: str, chat_history: list) -> str:
    print("🧠 [MANAGER] Запрос к RAG-системе...")
    found_knowledge = search_business_info(user_text)

    today = datetime.now().strftime("%d.%m.%Y")

    system_prompt = {
        "role": "system",
        "content": (
            "Ты — профессиональный ИИ-ассистент в барбершопе. "
            "Твоя задача — вежливо консультировать клиентов и помогать им оформить заявку на стрижку.\n\n"
            "Если у тебя есть Имя, Телефон, Дата и Время — напиши вежливое подтверждение и "
            "обязательно добавь в конце сообщения тег [ACTION:CREATE].\n"
            "Если данных не хватает — задай уточняющий вопрос.\n"
            "🚨 СТРОЖАЙШИЕ ПРАВИЛА:\n"
            "1. Говори точные цены и условия СТРОГО из секции 'БАЗА ЗНАНИЙ' ниже.\n"
            "2. Если нужной информации в базе нет, ответь строго: 'К сожалению, у меня нет точной информации по этому вопросу. Оставьте ваш номер телефона, и наш специалист свяжется с вами.'\n"
            "3. Будь краток и веди клиента к записи.\n"
            f"4. Сегодняшняя дата: {today} .\n"
            "5.Если клиент говорит 'завтра', вычисли дату как {datetime.now() + timedelta(days=1)} и запиши в формате ДД.ММ.ГГГГ. \n "
            "6.ПРАВИЛО ДАТЫ: Всегда преобразуй относительные даты (сегодня, завтра, 15 июня) в формат ДД.ММ.ГГГГ (например, 15.06.2026). Если клиент не назвал год — считай, что это текущий год. \n"
            "7. Если клиент задает вопросы за рамки барбершопа, стрижки или записи то говари что ты можешь ответить только на эти инфориации. \n "
            "8. Если клиент просит ПЕРЕНЕСТИ запись, уточни дату/время и добавь в конце тег [ACTION:UPDATE]. \n "
            "9. Если клиент хочет создать запись, используй [ACTION:CREATE]. \n "
            "10. Если клиент пишет время который уже прошел или уже близко наприер сейчас время 13:00 а клиент хочет записаться на 12:00 подправ клиента. \n "
            "НИКОГДА не используй [ACTION:CREATE], если клиент просит ПЕРЕНЕСТИ запись. \n "
            f"=== БАЗА ЗНАНИЙ ===\n{found_knowledge}\n=================="
        )
    }
    
    messages = [system_prompt] + chat_history
    
    try:
        response = await client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=0.3,
            
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ [MANAGER] Ошибка вызова LLM: {e}")
        return "Извините, щас минуту, напишите еще раз."