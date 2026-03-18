# test_db.py
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import os

DB_FAISS_PATH = "vectorstore/db_faiss"

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={'device': 'cpu'}
)

db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
print(f"Всего документов в базе: {db.index.ntotal}")

# Поиск по медицинским терминам
docs = db.similarity_search("медицинские данные пациенты ФЗ-152", k=5)
print("\nДокументы по медицинской теме:")
for doc in docs:
    print(f"- {doc.metadata.get('source', 'unknown')}")