# 🤖 Project.AI - Production-Ready Booking Bot SaaS


**Полностью готовая к production система для управления бронированиями через Telegram и WhatsApp**

### Что делает проект
Это проект на основе ИИ агентов Модел **Deepseek** для векторный базы данных я использую **ChromaDB**. ИИ агент manager_improved.py он общается с клиентом отвечает на вопросы и извликает от клиента имя, номер. агент extractor_improved.py принимает эти данные и сохрнаяет в Goolge таблицу.
---

## 📚 Документация
___
### tools 
1.RagCache: Простой кэш для RAG результатов
2.process_booking_request: Обрабатывает запрос на запись с проверкой занятости.
3.clean_and_repair_json: Очищает и восстанавливает JSON из ответа ИИ.
4.run_extractor_agent: Извлекает структурированные данные из истории чата.
5.search_business_info: функция который читает базу данных
6.rebuild_vector_store: Тяжелая функция для полной пересборки векторный базы данных.
___

### Стек проекта 
**Python, LangGraph, ChromaDB, aiogram, FastAPI**
___

## Быстрый старт 

```bash
# 1. Активировать виртуальное окружение
.venv\Scripts\Activate.ps1

# 2. Запустить Telegram бот
python main_tg_improved.py

# 3. В другом терминале запустить WhatsApp бот
python main_wa_improved.py

# 4. Проверить здоровье системы
curl http://localhost:8001/health
```

---

## 🎯 Что в проекте

### 📱 Боты (Production-ready)

```
main_tg_improved.py
├─ Rate limiting (10 req/min)
├─ Data validation (все входные данные)
├─ Background task execution
├─ Session cleanup (hourly)
└─ Comprehensive logging

main_wa_improved.py
├─ FastAPI webhook server
├─ /health endpoint (мониторинг)
├─ /metrics endpoint (статистика)
├─ Retry logic (3 attempts + backoff)
├─ Circuit breaker protection
└─ HTTP timeout (30 sec)
```

### 🤖 AI Agents

```
agents/manager_improved.py 
├─ RAG caching (1 hour TTL)
├─ LLM timeout (25 sec)
├─ History limit (50 messages)
└─ Error recovery

agents/extractor_improved.py 
├─ Safe JSON parsing
├─ Graceful fallback
├─ Markdown cleanup
└─ Type-safe extraction
```

###  Security & Monitoring

```
security.py
├─ RateLimiter (token bucket)
├─ DataValidator (phone, date, time)
└─ CircuitBreaker (fail-fast)

health_check.py
├─ System health checks
├─ Statistics collection
└─ Metrics endpoints
```

---

## Архитектура

```
Clients (Telegram + WhatsApp)
         ↓
Security Layer (Rate limit + Validation)
         ↓
Bot Processing (aiogram + FastAPI)
         ↓
AI Agents (Manager + Extractor)
         ↓
Data Layer (Google Sheets + Chroma DB)
         ↓
Monitoring (Health checks + Metrics)
```


---

##  Установка

### Требования

```
✓ Python 3.9+
✓ Telegram Token
✓ DeepSeek API key
✓ Google Sheets credentials
✓ (Optional) WhatsApp Business API
```

### Пошагово

```bash
# 1. Клонировать проект
cd Project.AI

# 2. Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\Activate.ps1

# 3. Установить зависимости
pip install -r requirements_clean.txt

# 4. Создать .env файл
copy .env.example .env
# Отредактируйте .env с вашими ключами

# 5. Инициализировать
python init_project.py

# 6. Запустить
python main_tg_improved.py
```

---

## ⚙️ Конфигурация

### Основные переменные .env

```env
# AI/LLM
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_MODEL=deepseek-chat

# Telegram
TELEGRAM_TOKEN=your_telegram_token

# WhatsApp
WHATSAPP_TOKEN=your_wa_token
VERIFY_TOKEN=your_webhook_token

# Google Sheets
GOOGLE_CREDENTIALS_JSON=/path/to/credentials.json

# System
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_REQUESTS_PER_MINUTE=10
```




---

## Docker

```bash
# Запустить в Docker
docker build -t project-ai .
docker run -p 8000:8000 -p 8001:8001 --env-file .env project-ai

# Или с Docker Compose
docker-compose up --build
```

---

## Структура файлов

```
Project.AI/
├──  Боты (Production)
│   ├── main_tg_improved.py
│   └── main_wa_improved.py
│
├──  Agents
│   ├── agents/manager_improved.py
│   ├── agents/extractor_improved.py
│   └── agents/rag_storage.py
│
├──  Core
│   ├── security.py
│   ├── health_check.py
│   └── error_handler.py
│
├──  Docs
│   ├── README.md (THIS)
│   ├── QUICKSTART.md
│   ├── MIGRATION_GUIDE.md
│   ├── SECURITY_AUDIT.md
│   └── STATISTICS.md
│
├──  Tools
│   ├── init_project.py
│   ├── duplicate_for_business.py
│   └── config_new.py
│
├──  Data
│   ├── database/sheets.py
│   ├── BASE_VECTOR/
│   └── chroma_db/
│
└── 🔧 Config
    ├── .env
    ├── .env.example
    └── requirements_clean.txt
```

---

##  Безопасность

### Встроенные защиты

 **Rate Limiting** - 10 запросов/минута на пользователя  
 **Input Validation** - Все входные данные проверены  
 **Timeout Protection** - 25-30 сек на все API запросы  
 **Circuit Breaker** - Защита от cascade failures  
 **Secure Logging** - Никаких чувствительных данных  
 **Error Recovery** - Автоматическое восстановление

---

## 🚨 Troubleshooting

### "Rate limit exceeded"
```
Это нормально - защита от spam
Увеличить: MAX_REQUESTS_PER_MINUTE = 20 в .env
```

### "Validation error"
```
Проверьте формат:
- Телефон: +996700123456
- Дата: 15.06.2026
- Время: 14:30
```

### Логи
```bash
# Смотреть логи
tail -f logs/app.log

# Фильтр по ошибкам
tail -f logs/app.log | grep ERROR
```

---

### Вопросы?

1. Прочитайте [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md#-faq)
2. Проверьте [SECURITY_AUDIT.md](SECURITY_AUDIT.md)
3. Смотрите логи: `tail -f logs/app.log`
4. Health check: `curl http://localhost:8001/health`
