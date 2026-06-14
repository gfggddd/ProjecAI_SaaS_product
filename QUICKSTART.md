# ⚡ QUICKSTART - За 5 минут до запуска

**Время:** 5 минут | **Сложность:** Easy | **Статус:** ✅ Production-Ready

---

## 🚀 Вариант 1: Локальный запуск (Recommended)

### Step 1: Активировать окружение (30 сек)

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux/Mac
source .venv/bin/activate
```

### Step 2: Создать .env файл (1 мин)

```bash
# Скопировать пример
copy .env.example .env
```

Отредактируйте `.env` с вашими ключами:

```env
DEEPSEEK_API_KEY=your_key_here
TELEGRAM_TOKEN=your_token_here
WHATSAPP_TOKEN=optional
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

### Step 3: Запустить Telegram бот (1 мин)

```bash
python main_tg_improved.py
```

Вы должны увидеть:
```
✅ Telegram bot started
✅ Health check passed
📍 Listening for messages...
```

### Step 4: (Optional) Запустить WhatsApp (2 мин)

В другом терминале:

```bash
python main_wa_improved.py
```

Вы должны увидеть:
```
✅ WhatsApp server started on port 8001
✅ Health check passed
📍 Webhook ready...
```

### Step 5: Проверить здоровье (30 сек)

```bash
curl http://localhost:8001/health
```

Вывод:
```json
{
  "status": "healthy",
  "components": {
    "filesystem": "healthy",
    "logging": "healthy",
    "config": "healthy"
  }
}
```

**✅ Готово! Система запущена и работает.**

---

## 🐳 Вариант 2: Docker (Для production)

### Step 1: Запустить (1 мин)

```bash
docker-compose up --build
```

### Step 2: Проверить (1 мин)

```bash
curl http://localhost:8001/health
```

---

## 🧪 Протестировать

### Telegram тест

1. Найдите вашего бота в Telegram
2. Отправьте: `"Запишу меня на стрижку на 15.06.2026 в 14:30"`
3. Бот должен ответить с подтверждением

### WhatsApp тест

1. Отправьте сообщение на ваш номер WhatsApp Business
2. Бот должен ответить автоматически

### Health endpoint

```bash
# Проверить метрики
curl http://localhost:8001/metrics | jq .

# Вывод:
{
  "uptime_seconds": 120,
  "request_count": 5,
  "error_count": 0,
  "error_rate": 0
}
```

---

## ⚙️ Конфигурация за 1 минуту

### Основные переменные

| Переменная | Обязательна | Описание |
|-----------|-----------|---------|
| DEEPSEEK_API_KEY | ✅ | API для AI |
| TELEGRAM_TOKEN | ✅ | Telegram бот токен |
| ENVIRONMENT | ❌ | development / production |
| LOG_LEVEL | ❌ | DEBUG / INFO / WARNING |

### Получить ключи

```
1. DeepSeek: https://platform.deepseek.com
2. Telegram: @BotFather в Telegram
3. Google Sheets: Google Cloud Console
```

---

## 🆘 Если не работает

### Error: "Rate limit exceeded"

```
✅ Это нормально - защита от spam
Увеличить в .env:
MAX_REQUESTS_PER_MINUTE=20
```

### Error: "DEEPSEEK_API_KEY not found"

```
✅ Проверить .env файл:
cat .env | grep DEEPSEEK
```

### Error: "Connection refused"

```
✅ Проверить что бот запущен:
ps aux | grep main_tg

✅ Перезагрузить:
Ctrl+C в терминале
python main_tg_improved.py
```

### Error: "Port 8001 already in use"

```
✅ Другой процесс использует порт
Решение:
lsof -i :8001
kill -9 <PID>

Или использовать другой порт в коде
```

---

## 📚 Дальше?

### Для полной документации

1. **[README.md](README.md)** - Полный обзор проекта
2. **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Как обновиться
3. **[SECURITY_AUDIT.md](SECURITY_AUDIT.md)** - Security details

### Для production

1. Прочитайте [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
2. Запустите в Docker (docker-compose)
3. Настройте мониторинг (health check)
4. Включите логирование (LOG_LEVEL=WARNING)

---

## ✨ Итого

**Вы только что:**
- ✅ Запустили production-ready систему
- ✅ Проверили здоровье компонентов
- ✅ Готовы к первому запросу

**Следующие шаги:**
1. Отредактируйте [BASE_VECTOR/barber_data.txt](BASE_VECTOR/barber_data.txt) под ваш бизнес
2. Прочитайте [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) для production
3. Настройте мониторинг и alerting

**Вопросы?** Смотрите [INDEX.md](INDEX.md) для файл-индекса 🎯

---

🚀 **Готово! Начните тестировать бота!**
