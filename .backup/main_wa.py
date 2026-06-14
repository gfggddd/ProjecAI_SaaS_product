import config
import asyncio
import aiohttp
from fastapi import FastAPI, Request, Response, Query
import uvicorn

from database.sheets import save_booking_async, modify_booking_async
from agents.manager import run_manager_agent
from agents.extractor import run_extractor_agent

app = FastAPI()

USER_SESSIONS = {}



def get_history(user_id: str) -> list:
    if user_id not in USER_SESSIONS: USER_SESSIONS[user_id] = []
    return USER_SESSIONS[user_id]

def add_to_history(user_id: str, role: str, content: str):
    history = get_history(user_id)
    history.append({"role": role, "content": content})
    if len(history) > 20: USER_SESSIONS[user_id] = history[-20:]

# 1. ОТПРАВКА ОТВЕТА В WHATSAPP (Официальный Cloud API / Meta)
async def send_whatsapp_message(to_phone: str, text: str):
    url = f"https://graph.facebook.com/v17.0/{config.WA_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {config.WA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text}
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status == 200:
                print(f"✉️ [WA] Сообщение успешно отправлено на номер {to_phone}")
            else:
                raw_err = await response.text()
                print(f"❌ [WA] Ошибка отправки сообщения: {raw_err}")

# 2. ВЕРИФИКАЦИЯ ВЕБХУКА (Нужна при первой привязке в панели Meta / Green-API)
@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(None, alias="hub.mode"),
    token: str = Query(None, alias="hub.verify_token"),
    challenge: str = Query(None, alias="hub.challenge")
):
    if mode == "subscribe" and token == config.WA_VERIFY_TOKEN:
        print("✅ [WA-WEBHOOK] Вебхук успешно верифицирован!")
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Ошибка верификации токена", status_code=403)

# 3. ПРИЕМ СООБЩЕНИЙ ИЗ WHATSAPP
@app.post("/webhook")
async def receive_whatsapp_message(request: Request):
    try:
        data = await request.json()
        print(f"📥 [WA-WEBHOOK] Получены новые данные: {data}")
        
        # Парсинг стандартного JSON от WhatsApp Cloud API
        if "entry" in data and data["entry"][0]["changes"][0]["value"].get("messages"):
            message_obj = data["entry"][0]["changes"][0]["value"]["messages"][0]
            wa_id = message_obj["from"]  # Номер телефона клиента (например, "996700123456")
            user_text = message_obj["text"]["body"]
            
            print(f"👤 [WA] Сообщение от {wa_id}: {user_text}")
            
            # Логика обработки ИИ (точно такая же, как в TG!)
            add_to_history(wa_id, "user", user_text)
            chat_history = get_history(wa_id)
            
            manager_reply = await run_manager_agent(user_text, chat_history)
            add_to_history(wa_id, "assistant", manager_reply)
            
            # Отвечаем клиенту в WhatsApp
            await send_whatsapp_message(wa_id, manager_reply)
            
            # Триггеры CRM
            triggers = ["записал", "оформил", "заявка принята", "подтверждаю", "отменил", "перенес", "обновил"]
            if any(tg in manager_reply.lower() for tg in triggers):
                print(f"🔔 [WA-ROUTER] Запуск экстрактора для номера {wa_id}...")
                extracted = await run_extractor_agent(chat_history)
                
                action = extracted["action"]
                name = extracted["name"]
                phone = extracted["phone"] if extracted["phone"] != "Не указано" else wa_id
                date = extracted["date"]
                time = extracted["time"]
                service = extracted["service"]
                
                if action == "create":
                    asyncio.create_task(save_booking_async(name, phone, date, time, service))
                    print("✅ [WA] Задача на создание записи отправлена в фон.")
                elif action in ["update", "cancel"]:
                    asyncio.create_task(modify_booking_async(phone, action, date, time))
                    print(f"✅ [WA] Задача на {action} отправлена в фон.")
                    
    except Exception as e:
        print(f"❌ [WA-WEBHOOK] Ошибка обработки запроса: {e}")
        
    return {"status": "ok"}

if __name__ == "__main__":
    print(f"🚀 [WHATSAPP-SERVER] Запуск сервера вебхуков на порту {config.PORT_WA}...")
    uvicorn.run("main_wa.py:app", host="0.0.0.0", port=config.PORT_WA, reload=False)