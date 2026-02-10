import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

SOURCES_DIR = "sources"
DB_FAISS_PATH = "vectorstore/db_faiss"


def create_vector_db():
    print("🔄 Начинаю сканирование файлов разных форматов...")
    documents = []

    if not os.path.exists(SOURCES_DIR):
        os.makedirs(SOURCES_DIR)
        print(f"❌ Папка {SOURCES_DIR} не найдена.")
        return

    for file in os.listdir(SOURCES_DIR):
        file_path = os.path.join(SOURCES_DIR, file)

        try:
            # Читаем PDF
            if file.endswith('.pdf'):
                print(f"📄 Чтение PDF: {file}")
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())

            # Читаем обычный текст
            elif file.endswith('.txt'):
                print(f"📝 Чтение TXT: {file}")
                loader = TextLoader(file_path, encoding='utf-8')
                documents.extend(loader.load())

            # Читаем Word (нужно установить: pip install unstructured python-docx)
            elif file.endswith('.docx'):
                print(f"📂 Чтение DOCX: {file}")
                loader = UnstructuredWordDocumentLoader(file_path)
                documents.extend(loader.load())

        except Exception as e:
            print(f"⚠️ Ошибка при чтении {file}: {e}")

    if not documents:
        print("⚠️ Документы не найдены.")
        return

    # Разбиваем на фрагменты
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = text_splitter.split_documents(documents)
    print(f"🧩 Итого: {len(texts)} фрагментов текста.")

    # Векторизация
    print("🧠 Загрузка модели эмбеддингов...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("💾 Сохранение базы знаний...")
    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_FAISS_PATH)
    print(f"✅ Готово! База знаний обновлена.")


if __name__ == "__main__":
    create_vector_db()