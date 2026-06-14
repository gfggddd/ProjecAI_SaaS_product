import json
import asyncio
import config_new as config
from logger_config import logger
from error_handler import ExternalAPIError
from openai import AsyncOpenAI, APIError
from typing import Dict

client = AsyncOpenAI(
    api_key=config.DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com",
    timeout=20.0
)

def clean_and_repair_json(raw_text: str) -> dict:
    """Очищает и восстанавливает JSON из ответа ИИ."""
    try:
        cleaned = raw_text.strip()
        
        # Удаляем markdown код блоки
        if cleaned.startswith("```"):
            cleaned = cleaned.split("\n", 1)[-1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("\n", 1)[0]
        
        cleaned = cleaned.strip().lstrip("json").strip()
        
        # Пытаемся распарсить JSON
        data = json.loads(cleaned)
        
        # Убеждаемся что все ключи присутствуют
        required_keys = ["action", "name", "phone", "date", "time",]
        for key in required_keys:
            if key not in data or not data[key]:
                data[key] = "Не указано"
        
        # Валидируем action
        if data["action"] not in ["create", "update", "cancel"]:
            data["action"] = "create"
        
        logger.debug(f"JSON parsed successfully: {data['action']}")
        return data
    
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}, using fallback")
        return {
            "action": "create",
            "name": "Не указано",
            "phone": "Не указано",
            "date": "Не указано",
            "time": "Не указано",
        }

async def run_extractor_agent(chat_history: list) -> Dict[str, str]:
    """
    Извлекает структурированные данные из истории чата.
    """
    try:
        # Берём последние 30 сообщений для контекста
        context_messages = chat_history[-30:] if len(chat_history) > 30 else chat_history
        
        system_prompt = {
            "role": "system",
            "content": (
                "Ты — экстрактор данных. Твоя задача — вытащить из диалога:\n"
                "1. action: create (новая запись), update (перенос), cancel (отмена)\n"
                "2. name: имя клиента\n"
                "3. phone: номер телефона\n"
                "4. date: дата (ДД.ММ.ГГГГ)\n"
                "5. time: время (ЧЧ:ММ)\n"
                "Ответь ТОЛЬКО чистым JSON объектом. Если данных нет, напиши 'Не указано'.\n"
                "Пример: {\"action\": \"create\", \"name\": \"Иван\", ...}"
            )
        }
        
        messages = [system_prompt] + context_messages
        
        # Запрос к LLM
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=0.0,
                max_tokens=200,
                response_format={"type": "json_object"}
            ),
            timeout=15.0
        )
        
        raw_content = response.choices[0].message.content
        data = clean_and_repair_json(raw_content)
        
        logger.debug(f"Extracted data: {data['action']} for {data.get('phone', 'unknown')}")
        return data
    
    except asyncio.TimeoutError:
        logger.error("Extractor timeout")
        return {
            "action": "create",
            "name": "Не указано",
            "phone": "Не указано",
            "date": "Не указано",
            "time": "Не указано",
        }
    
    except APIError as e:
        logger.error(f"Extractor API error: {e}")
        return {
            "action": "create",
            "name": "Не указано",
            "phone": "Не указано",
            "date": "Не указано",
            "time": "Не указано",
        }
    
    except Exception as e:
        logger.error(f"Unexpected error in extractor: {e}")
        return {
            "action": "create",
            "name": "Не указано",
            "phone": "Не указано",
            "date": "Не указано",
            "time": "Не указано",
        }
