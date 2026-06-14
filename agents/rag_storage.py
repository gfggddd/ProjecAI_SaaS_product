import sys
import os

# Получаем путь к корню проекта (Project.AI)
# os.path.dirname(os.path.abspath(__file__)) — это путь к папке agents
# os.path.dirname(...) — поднимаемся на уровень выше в Project.AI
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if root_path not in sys.path:
    sys.path.append(root_path)

import config_new as config
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
import logging

# Настройка логов, чтобы видеть, что происходит
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация модели (кешируется при импорте)
embedding_model = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL_NAME)

def search_business_info(query: str) -> str:
    """Легкая функция только для чтения базы."""
    try:
        vector_store = Chroma(
            persist_directory=config.PERSIST_DIRECTORY, 
            embedding_function=embedding_model
        )
        docs = vector_store.similarity_search(query, k=5)
        return "\n---\n".join([d.page_content for d in docs])
    except Exception as e:
        logger.error(f"Ошибка при поиске в базе: {e}")
        return ""

def rebuild_vector_store():
    """Тяжелая функция для полной пересборки базы."""
    import shutil
    import os
    from langchain_core.documents import Document

    logger.info("🔄 Начало процесса пересборки базы векторов...")

    # 1. Удаляем старую базу, если она есть
    if os.path.exists(config.PERSIST_DIRECTORY):
        shutil.rmtree(config.PERSIST_DIRECTORY)
        logger.info(f"🗑 Папка {config.PERSIST_DIRECTORY} удалена.")

    # 2. Читаем новые данные
    if not os.path.exists(config.VECTOR_DATA_FILE):
        logger.error(f"❌ Файл данных не найден: {config.VECTOR_DATA_FILE}")
        return

    with open(config.VECTOR_DATA_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        manual_chunks = [p.strip() for p in content.split("\n\n") if p.strip()]

    # 3. Создаем новую базу
    if manual_chunks:
        Chroma.from_documents(
            documents=[Document(page_content=text) for text in manual_chunks],
            embedding=embedding_model,
            persist_directory=config.PERSIST_DIRECTORY
        )
        logger.info(f"✅ База успешно создана. Загружено сегментов: {len(manual_chunks)}")
    else:
        logger.warning("⚠️ Файл данных пуст, база не создана.")

if __name__ == "__main__":
    # Запуск пересборки только при прямом вызове файла
    rebuild_vector_store()