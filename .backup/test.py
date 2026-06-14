import asyncio
from database.sheets import save_booking_async

async def main():
    print("Пробую записать тестовые данные...")
    success = await save_booking_async("Иван", "+996555000000", "2026-05-28", "14:00", "Стрижка")
    if success:
        print("ГОТОВО! Данные улетели в таблицу.")
    else:
        print("ОШИБКА! Проверь консоль выше.")

asyncio.run(main())