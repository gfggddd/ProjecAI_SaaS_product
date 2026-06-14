import sys
import os

# Получаем путь к корню проекта (Project.AI)
# os.path.dirname(os.path.abspath(__file__)) — это путь к папке agents
# os.path.dirname(...) — поднимаемся на уровень выше в Project.AI
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if root_path not in sys.path:
    sys.path.append(root_path)

import json
import config
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=config.DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")

def clean_and_repair_json(raw_text: str) -> dict:
    """Очищает ответ ИИ от markdown-тегов и проверяет структуру."""
    cleaned = raw_text.strip()
    
    # Удаляем кавычки ```json, если они вдруг появились
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("\n", 1)[0]
    cleaned = cleaned.strip().lstrip("json").strip()

    required_keys = ["action", "name", "phone", "date", "time", "service"]
    try:
        data = json.loads(cleaned)
    except Exception:
        print("⚠️ [EXTRACTOR] Не удалось распарсить JSON. Применяется безопасный fallback.")
        data = {}
        
    # Проверяем, чтобы каждый нужный ключ точно был в словаре
    for key in required_keys:
        if key not in data or not data[key]:
            data[key] = "Не указано"
            
    if data["action"] not in ["create", "update", "cancel"]:
        data["action"] = "create"
        
    return data # Теперь функция возвращает ГОТОВЫЙ словарь, а не текст

async def run_extractor_agent(chat_history: list) -> dict:
    """
    Читает историю и вытаскивает переменные.
    """
    print("🧠 [EXTRACTOR] Извлечение сущностей из диалога...")
    
    system_prompt = {
        "role": "system",
        "content": (
            "Ты — системный робот-экстрактор данных. Твоя задача — вытащить параметры сделки из диалога.\n"
            "Верни ответ СТРОГО в формате чистого JSON объекта со следующими ключами:\n"
            "1. \"action\" — строго одно из трех значений: \"create\" (новая запись), \"update\" (перенос), \"cancel\" (отмена)\n"
            "2. \"name\" — имя клиента\n"
            "3. \"phone\" — телефон\n"
            "4. \"date\" — дата\n"
            "5. \"time\" — время\n"
            "6. \"service\" — запрашиваемая услуга\n\n"
            "Если значения нет, пиши \"Не указано\". Никакого лишнего текста, только JSON."
        )
    }
    
    messages = [system_prompt] + chat_history
    
    try:
        response = await client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        raw_content = response.choices[0].message.content
        return clean_and_repair_json(raw_content)
        
    except Exception as e:
        print(f"❌ [EXTRACTOR] Критическая ошибка: {e}")
        # Если упал интернет, возвращаем безопасный словарь, чтобы бот не вылетел
        return {"action": "create", "name": "Ошибка", "phone": "Ошибка", "date": "Ошибка", "time": "Ошибка", "service": "Ошибка"}