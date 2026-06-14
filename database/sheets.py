import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config_new as config
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# --- КОНФИГУРАЦИЯ ---
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
sheet_lock = asyncio.Lock()

def get_sheet():
    creds = ServiceAccountCredentials.from_json_keyfile_name(config.CREDS_PATH, SCOPE)
    client = gspread.authorize(creds)
    # Открываем лист (убедись, что config.SPREADSHEET_NAME настроен правильно)
    return client.open(config.SPREADSHEET_NAME).sheet1

# --- ЧТЕНИЕ ---
def sync_get_all_bookings():
    sheet = get_sheet()
    data = sheet.get_all_values()
    # Возвращаем список словарей, пропуская заголовок (data[1:])
    return [{"name": r[0], "phone": r[1], "date": r[2], "time": r[3], "service": r[4], "status": r[5]} 
            for r in data[1:] if len(r) >= 6 and r[5] != "❌ Отменено"]

async def get_all_bookings_async():
    return await asyncio.to_thread(sync_get_all_bookings)

# --- ЗАПИСЬ (СОЗДАНИЕ) ---
def sync_save_booking(name, phone, date, time, service):
    sheet = get_sheet()
    all_data = sheet.get_all_values()
    req_time = datetime.strptime(time, "%H:%M")
    
    # Проверка на занятость 30 минут
    for row in all_data[1:]:
        if len(row) > 3 and row[2] == date and row[5] != "❌ Отменено":
            booked_time_str = row[3]
            try:
                booked_time = datetime.strptime(booked_time_str, "%H:%M")
                if abs((req_time - booked_time).total_seconds()) / 60 < 30:
                    return "BUSY"
            except ValueError:
                continue

    sheet.append_row([name, phone, date, time, service, "✅ Подтверждено"])
    return True

async def save_booking_async(n, p, d, t, s):
    async with sheet_lock: 
        return await asyncio.to_thread(sync_save_booking, n, p, d, t, s)

# --- МОДИФИКАЦИЯ (ОБНОВЛЕНИЕ) ---
def sync_modify_booking(phone, action, new_date, new_time):
    sheet = get_sheet()
    rows = sheet.get_all_values()
    clean_phone = str(phone).replace(" ", "").replace("+", "")
    
    # 1. ПРОВЕРКА НА ЗАНЯТОСТЬ ПРИ ПЕРЕНОСЕ
    if action == "update" and new_time:
        new_time_dt = datetime.strptime(new_time, "%H:%M")
        for row in rows[1:]:
            # Пропускаем отмененные и самого клиента
            if row[5] == "❌ Отменено" or str(row[1]).replace(" ", "").replace("+", "") == clean_phone:
                continue
            if len(row) > 3 and row[2] == new_date:
                try:
                    booked_time = datetime.strptime(row[3], "%H:%M")
                    if abs((new_time_dt - booked_time).total_seconds()) / 60 < 30:
                        return "BUSY"
                except ValueError:
                    continue

    # 2. ВЫПОЛНЕНИЕ ОБНОВЛЕНИЯ
    for i, row in enumerate(rows[1:]):
        if str(row[1]).replace(" ", "").replace("+", "") == clean_phone and row[5] != "❌ Отменено":
            idx = i + 2 # Индекс строки для gspread
            if action == "cancel": 
                sheet.update_cell(idx, 6, "❌ Отменено")
            elif action == "update":
                if new_date: sheet.update_cell(idx, 3, new_date)
                if new_time: sheet.update_cell(idx, 4, new_time)
                sheet.update_cell(idx, 6, "🔄 Изменено")
            return True
    return False

async def modify_booking_async(p, action, d=None, t=None):
    async with sheet_lock: 
        return await asyncio.to_thread(sync_modify_booking, p, action, d, t)