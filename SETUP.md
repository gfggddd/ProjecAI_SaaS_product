# Детальная инструкция по настройке BarberBot AI

## 🚀 Полная инструкция установки

### Шаг 1: Подготовка окружения

#### Windows
```bash
# Откройте PowerShell и выполните:
python -m venv .venv
.venv\Scripts\activate
```

#### Linux/Mac
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Шаг 2: Установка зависимостей

```bash
pip install --upgrade pip
pip install -r requirements_clean.txt
```

### Шаг 3: Инициализация проекта

```bash
python init_project.py
```

Скрипт автоматически:
- Создаст необходимые папки (logs, chroma_db и т.д.)
- Скопирует .env.example в .env
- Проверит зависимости
- Даст подсказки что делать дальше

---

## 🔑 Получение необходимых ключей и токенов

### 1. DeepSeek API Key

**Обязательно для работы ИИ!**

1. Перейдите на https://platform.deepseek.com
2. Создайте аккаунт (можно через email или GitHub)
3. В левом меню выберите "API Keys"
4. Нажмите "Create new secret key"
5. Скопируйте ключ (выглядит как `sk-xxxxxx...`)
6. Откройте `.env` и вставьте:
   ```
   DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxx
   ```

**Важно:** 
- Ключ используется для запросов к ИИ модели
- У вас должна быть подписка с кредитами (или Trial для тестирования)
- Проверьте баланс на платформе

### 2. Telegram Bot Token

**Нужен для Telegram бота**

1. Откройте Telegram и напишите боту @BotFather
2. Отправьте команду `/newbot`
3. Следуйте инструкциям:
   - Дайте боту имя (например "BarberBookingBot")
   - Дайте юзернейм (должен заканчиваться на "_bot", например "@barber_booking_bot")
4. BotFather вернёт токен (выглядит как `123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi`)
5. Вставьте в `.env`:
   ```
   TELEGRAM_TOKEN=123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi
   TELEGRAM_ADMIN_ID=ваш_личный_id
   ```

**Как узнать ваш ID в Telegram:**
- Напишите боту @userinfobot
- Он ответит вашим ID
- Скопируйте число в TELEGRAM_ADMIN_ID

### 3. Google Sheets Credentials (опционально)

**Нужно для сохранения записей в Google Таблицы**

1. Откройте https://console.cloud.google.com
2. Создайте новый проект
3. Включите Google Sheets API:
   - В поиске найдите "Google Sheets API"
   - Нажмите "Enable"
4. Создайте Service Account:
   - Слева меню → "Service Accounts"
   - "Create Service Account"
   - Дайте имя (например "barberbot-sa")
5. Создайте ключ:
   - Выберите Service Account
   - Вкладка "Keys" → "Add Key" → "Create new key"
   - Выберите JSON
   - Скачайте файл
6. Переименуйте скачанный файл в `creds.json` и положите в корень проекта

7. Поделитесь Google Sheet с Service Account:
   - Откройте JSON файл и скопируйте email из поля `client_email`
   - Откройте вашу Google Sheet (для записей клиентов)
   - Поделитесь ею (Share) с этим email
   - Убедитесь что выбран доступ "Editor"

8. В `.env`:
   ```
   CREDS_PATH=./creds.json
   SPREADSHEET_NAME=BarBershop client
   ```

**Структура Google Sheet должна быть:**
| Имя | Номер | Дата | Время | Услуга | Статус |
|-----|-------|------|-------|--------|--------|

### 4. WhatsApp Cloud API (опционально)

**Нужно для интеграции с WhatsApp**

1. Создайте бизнес-аккаунт на Meta: https://business.facebook.com
2. Пройдите верификацию
3. В Meta Business Suite:
   - Выберите бизнес-приложение
   - Найдите "WhatsApp" → "Getting Started"
4. Получите:
   - **Access Token** → вставьте в `WA_TOKEN`
   - **Phone Number ID** → вставьте в `WA_PHONE_NUMBER_ID`

5. Настройте вебхук:
   - В настройках приложения → "Webhooks"
   - URL: `https://ваш-сервер:8001/webhook`
   - Verify Token: придумайте и вставьте в `WA_VERIFY_TOKEN`

6. В `.env`:
   ```
   WA_TOKEN=your_access_token
   WA_PHONE_NUMBER_ID=your_phone_id
   WA_VERIFY_TOKEN=your_verify_token
   WA_PORT=8001
   ENABLE_WHATSAPP=True
   ```

---

## ⚙️ Конфигурация вашего бизнеса

### 1. Отредактируйте информацию о бизнесе

Откройте `BASE_VECTOR/barber_data.txt` и замените пример:

```
НАЗВАНИЕ БИЗНЕСА: BarberShop "Alex"
КОНТАКТЫ: 
  Телефон: +996 (555) 123-456
  Адрес: Бишкек, ул. Чуй 123
  Instagram: @barber_alex

УСЛУГИ И ЦЕНЫ:
  1. Стрижка классическая - 250 сом (30 мин)
  2. Стрижка с бородой - 350 сом (45 мин)
  3. Королевское бритьё - 200 сом (20 мин)
  4. Fade стрижка - 300 сом (40 мин)

МАСТЕРА:
  МАСТЕР: Алекс. РАНГ: Главный мастер. Работает все дни.
  МАСТЕР: Иван. РАНГ: Мастер. Выходной по понедельникам.

ГРАФИК РАБОТЫ:
  Пн-Пт: 10:00 - 20:00
  Сб-Вс: 11:00 - 18:00

СПЕЦИАЛЬНЫЕ ПРЕДЛОЖЕНИЯ:
  - Первая стрижка на 10% дешевле
  - Постоянным клиентам скидка 20%
```

### 2. Установите параметры в `.env`

```
BUSINESS_NAME=BarberShop Alex
BUSINESS_TIMEZONE=Asia/Bishkek
BOOKING_BUFFER_MINUTES=30
ENABLE_TELEGRAM=True
ENABLE_WHATSAPP=False
```

### 3. Выберите тип бизнеса

Если вы используете другой тип бизнеса (салон, клиника, фитнес), отредактируйте `constants.py`:

- BARBERSHOP_TEMPLATE - для барбершопа
- BEAUTY_SALON_TEMPLATE - для салона красоты
- GYM_TEMPLATE - для фитнес-центра
- CLINIC_TEMPLATE - для клиники/врача

---

## 🧪 Тестирование перед запуском

### 1. Проверка конфигурации

```bash
python -c "import config_new as config; print('✅ Конфиг OK')"
```

### 2. Проверка подключения к APIs

```bash
# Проверка DeepSeek
python -c "
from openai import AsyncOpenAI
import config_new as config
client = AsyncOpenAI(api_key=config.DEEPSEEK_API_KEY, base_url='https://api.deepseek.com')
print('✅ DeepSeek подключение OK')
"

# Проверка Google Sheets (если используется)
python -c "
from database.sheets import get_sheet
sheet = get_sheet()
print('✅ Google Sheets подключение OK')
"
```

### 3. Проверка логирования

```bash
python -c "
from logger_config import logger
logger.info('✅ Логирование работает')
"
```

### 4. Запуск в режиме тестирования

```bash
# Только Telegram
python main_tg.py

# В другом терминале протестируйте отправив сообщение боту
# Смотрите вывод в первом терминале
```

---

## 🚀 Запуск в Production

### Вариант 1: На локальной машине

```bash
# Telegram только
python main_tg.py

# WhatsApp только
python main_wa.py

# Оба одновременно
python run_all.py
```

### Вариант 2: На сервере (Linux/Ubuntu)

```bash
# 1. Установите Python и зависимости
sudo apt update && sudo apt install python3.11 python3-pip python3-venv

# 2. Клонируйте проект
git clone <repo-url>
cd Project.AI

# 3. Создайте virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# 4. Установите зависимости
pip install -r requirements_clean.txt

# 5. Инициализируйте проект
python init_project.py

# 6. Отредактируйте .env с вашими ключами
nano .env

# 7. Запустите бота в фоновом режиме
nohup python main_tg.py > logs/telegram.log 2>&1 &
nohup python main_wa.py > logs/whatsapp.log 2>&1 &

# Проверить статус
ps aux | grep python | grep main
```

### Вариант 3: Docker

```bash
# 1. Убедитесь что Docker установлен
docker --version

# 2. Создайте .env с вашими параметрами
cp .env.example .env
nano .env

# 3. Собрите образ
docker build -t barberbot-ai .

# 4. Запустите контейнер
docker run -p 8001:8001 --env-file .env barberbot-ai

# Или с Docker Compose (включает БД и Redis)
docker-compose up -d
```

---

## 📊 Структура Google Sheets для записей

**Название листа:** "BarBershop client" (или как указано в SPREADSHEET_NAME)

**Колонки:**
1. **A** - Имя клиента (например: "Иван")
2. **B** - Номер телефона (например: "+996555000000")
3. **C** - Дата (формат: ДД.ММ.ГГГГ, например: "28.05.2026")
4. **D** - Время (формат: ЧЧ:ММ, например: "14:00")
5. **E** - Услуга (например: "Стрижка классическая")
6. **F** - Статус (будет заполняться автоматически: ✅/🔄/❌)

**Пример строки:**
| Иван | +996555000000 | 28.05.2026 | 14:00 | Стрижка классическая | ✅ Подтверждено |

---

## 🐛 Отладка проблем

### Проблема: "DEEPSEEK_API_KEY отсутствует"

**Решение:**
1. Откройте `.env`
2. Убедитесь что есть строка `DEEPSEEK_API_KEY=sk-xxxxx`
3. Перезагрузите приложение

### Проблема: "Бот не отвечает в Telegram"

**Решение:**
1. Проверьте что боту написали правильное имя (@ваш_username_bot)
2. Посмотрите логи: `tail -f logs/app.log`
3. Убедитесь что TELEGRAM_TOKEN корректный
4. Проверьте интернет соединение

### Проблема: "Google Sheets не сохраняет"

**Решение:**
1. Проверьте что creds.json в корне проекта
2. Убедитесь что Service Account поделился Sheet с доступом "Editor"
3. Проверьте что SPREADSHEET_NAME совпадает с реальным названием
4. Посмотрите ошибки в логах

### Проблема: "WhatsApp вебхук не работает"

**Решение:**
1. Убедитесь что сервер имеет публичный IP
2. Настройте https (не http)
3. В Meta Business укажите правильный URL: `https://ваш-сервер:8001/webhook`
4. Verify Token должен совпадать в .env и Meta
5. Проверьте firewalls/порты

---

## 📈 Мониторинг в Production

### Просмотр логов

```bash
# Последние 50 строк логов
tail -50 logs/app.log

# Следящий режим (live)
tail -f logs/app.log

# Поиск ошибок
grep ERROR logs/app.log

# Статистика по ошибкам
grep -o '\[.*\]' logs/app.log | sort | uniq -c
```

### Проверка работающих процессов

```bash
# Все Python процессы
ps aux | grep python

# Только боты
ps aux | grep main_

# Статус сервиса (если настроена systemd служба)
systemctl status barberbot
```

---

## 🔄 Обновления и обслуживание

### Обновить код

```bash
git pull origin main
pip install --upgrade -r requirements_clean.txt
python init_project.py
```

### Ротация ключей API

```bash
# 1. Получите новый ключ на платформе (DeepSeek, Telegram и т.д.)
# 2. Обновите в .env
# 3. Перезагрузите приложение
# 4. Проверьте логи что всё работает
# 5. Удалите старый ключ на платформе
```

---

## 🎓 Дополнительные ресурсы

- **DeepSeek Документация:** https://platform.deepseek.com/docs
- **Telegram Bot API:** https://core.telegram.org/bots/api
- **aiogram документация:** https://docs.aiogram.dev/
- **Google Sheets API:** https://developers.google.com/sheets/api
- **WhatsApp Cloud API:** https://developers.facebook.com/docs/whatsapp/cloud-api

---

**Если у вас возникли проблемы, проверьте логи в `logs/app.log` - там будет подробная информация об ошибке!** 🔍
