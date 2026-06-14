import asyncio
import uvicorn
import config

# Импортируем настроенные диспетчер и бот из Telegram-модуля
from main_tg import dp, bot
# Импортируем FastAPI приложение из WhatsApp-модуля
from main_wa import app

async def main():
    print("==================================================")
    print("🚀 [AQUA-CORE] Запуск объединенного ИИ-сервера...")
    print("==================================================")

    # 1. Настраиваем сервер Uvicorn для WhatsApp программно
    # Указываем loop="asyncio", чтобы он работал в общем потоке
    config_wa = uvicorn.Config(
        app=app, 
        host="0.0.0.0", 
        port=config.PORT_WA, 
        loop="asyncio",
        log_level="info"
    )
    server_wa = uvicorn.Server(config_wa)

    # 2. Запускаем обе службы параллельно через asyncio.gather
    # Теперь один поток процессора будет молниеносно переключаться 
    # между опросом Telegram и приемом вебхуков WhatsApp
    await asyncio.gather(
        dp.start_polling(bot),  # Поток Telegram
        server_wa.serve()       # Поток WhatsApp
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 [AQUA-CORE] Сервер успешно остановлен.")