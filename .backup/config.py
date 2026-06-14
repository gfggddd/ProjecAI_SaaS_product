import os

# ОБЩИЕ НАСТРОЙКИ ЯДРА
DEEPSEEK_API_KEY = "sk-61fbe82ed3924553ac532e937d27ed3c"
LLM_MODEL = "deepseek-chat"

# Получаем путь к папке barber_bot (где лежит config.py)
import os

# Теперь BASE_DIR — это прямо папка Project.AI
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Абсолютные пути строятся прямо от корня
VECTOR_DATA_FILE = os.path.join(BASE_DIR, "base_vector", "barber_data.txt")
PERSIST_DIRECTORY = os.path.join(BASE_DIR, "chroma_db")

EMBEDDING_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# НАСТРОЙКИ БАЗЫ ДАННЫХ
CREDS_PATH = r"C:\Users\User\Desktop\Project.AI\creds.json" 
SPREADSHEET_NAME = "BarBershop client" 

# НАСТРОЙКИ TELEGRAM (aiogram / Polling)
TELEGRAM_TOKEN = "8902640296:AAG6F_BaFgVptWV1hdhEdSV_-LSmH2Tcfik"
ADMIN_ID = 6567766751

# НАСТРОЙКИ WHATSAPP (FastAPI / Webhook)
# Эти данные берутся из твоего личного кабинета провайдера WhatsApp API
WA_TOKEN = "ТВОЙ_ТОКЕН_WHATSAPP"
WA_PHONE_NUMBER_ID = "ТВОЙ_ID_ТЕЛЕФОНА_WHATSAPP"
WA_VERIFY_TOKEN = "my_secret_token_123"  # Токен для верификации вебхука в Meta/Green-API
PORT_WA = 5000  # Порт, на котором будет висеть вебхук WhatsApp

CHROMA_DB_PATH = "./chroma_db"

# Имя коллекции, которую ты создал в rag_storage.py (проверь, чтобы название совпадало!)
CHROMA_COLLECTION_NAME = "barber_knowledge"