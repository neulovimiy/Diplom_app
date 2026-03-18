import os
from striprtf.striprtf import rtf_to_text
from langchain_community.document_loaders import PyPDFLoader, TextLoader, UnstructuredWordDocumentLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

SOURCES_DIR = "sources"
DB_FAISS_PATH = "vectorstore/db_faiss"


def read_rtf(file_path):
    """Чтение RTF без Pandoc с помощью striprtf"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    return rtf_to_text(content)


def create_vector_db():
    print("🔄 Начинаю индексацию документов...")
    documents = []

    if not os.path.exists(SOURCES_DIR):
        print(f"❌ Папка {SOURCES_DIR} не найдена.")
        return

    for file in os.listdir(SOURCES_DIR):
        file_path = os.path.join(SOURCES_DIR, file)

        try:
            print(f"📄 Чтение файла: {file}")

            # 1. PDF
            if file.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
                docs = loader.load()

            # 2. TXT
            elif file.endswith('.txt'):
                loader = TextLoader(file_path, encoding='utf-8')
                docs = loader.load()

            # 3. DOCX
            elif file.endswith('.docx'):
                loader = UnstructuredWordDocumentLoader(file_path)
                docs = loader.load()

            # 4. RTF (НАШ НОВЫЙ МЕТОД)
            elif file.endswith('.rtf'):
                text = read_rtf(file_path)
                docs = [Document(page_content=text, metadata={'source': file})]

            else:
                continue

            # Добавляем метаданные к каждому документу
            for doc in docs:
                doc.metadata['source_file'] = file

            documents.extend(docs)

        except Exception as e:
            print(f"⚠️ Ошибка при чтении {file}: {e}")

    if not documents:
        print("⚠️ Документы не найдены.")
        return

    # Разбивка на фрагменты: 1200 - объем, 300 - нахлест (чтобы не терять контекст)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=300)
    texts = text_splitter.split_documents(documents)

    print(f"🧩 Итого фрагментов текста: {len(texts)}")

    # Загрузка модели эмбеддингов
    print("🧠 Инициализация модели эмбеддингов...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

    print("💾 Сохранение базы знаний в vectorstore/db_faiss...")
    if not os.path.exists("vectorstore"):
        os.makedirs("vectorstore")

    db = FAISS.from_documents(texts, embeddings)
    db.save_local(DB_FAISS_PATH)
    print("✅ Успешно! База знаний готова к использованию.")


if __name__ == "__main__":
    create_vector_db()