# modules/ai_analyst.py
import os
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

DB_FAISS_PATH = "vectorstore/db_faiss"


def format_docs(docs):
    """Форматирует документы для 100 источников: четкое разделение файлов"""
    formatted = []
    for doc in docs:
        source = os.path.basename(doc.metadata.get('source', 'Источник'))
        page = doc.metadata.get('page', '?')
        content = doc.page_content.replace('\n', ' ').strip()
        # Добавляем разделитель для ИИ, чтобы он видел границы файлов
        formatted.append(
            f"--- НАЧАЛО ФРАГМЕНТА ---\nИМЯ ФАЙЛА: {source}\nСТРАНИЦА: {page}\nТЕКСТ: {content}\n--- КОНЕЦ ФРАГМЕНТА ---")
    return "\n\n".join(formatted)


def format_learning_context(examples):
    if not examples: return "Это первая оценка."
    formatted = "ЖУРНАЛ ПРОШЛОГО ОПЫТА (для стиля):\n"
    for ex in examples:
        formatted += f"- Ресурс: {ex[0]} | Ранг: {ex[7]} [Ф:{ex[1]}, О:{ex[2]}, Ю:{ex[3]}, Р:{ex[4]}, С:{ex[5]}]\n"
    return formatted


# Справочник «Железная логика» (чтобы ИИ не галлюцинировал с номерами законов)
STRICT_LEGAL_MAP = """
СПРАВОЧНИК ЗАКОНОВ (ИСПОЛЬЗУЙ СТРОГО):
1. Интеллектуальная собственность (ПО, алгоритмы, чертежи) — Гражданский Кодекс РФ Часть 4.
2. Персональные данные — ФЗ-152.
3. Коммерческая тайна — ФЗ-98.
4. Информация и защита информации (общие нормы) — ФЗ-149.
5. Электронная подпись — ФЗ-63.
6. КИИ — ФЗ-187.
7. Банковская тайна — ФЗ-395-1.
"""


def get_ai_recommendation(resource_name, resource_description, resource_category, past_examples=[]):
    """Первичная оценка: Глубокий поиск по 100 источникам"""
    # Мы увеличиваем контекст до 12800 токенов, чтобы модель не забывала инструкции
    llm = OllamaLLM(model="deepseek-r1:8b", temperature=0.1, num_ctx=12800)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)

    # При 100 документах k=15 — это предел, чтобы не запутать модель
    retriever = db.as_retriever(search_kwargs={'k': 15})

    memory_text = format_learning_context(past_examples)

    template = """
    ИНСТРУКЦИЯ: Ты — эксперт-аудитор высшей категории. 
    ТВОЯ ЗАДАЧА: Определить ценность ресурса "{name}" через УЩЕРБ от его потери.
    ОТВЕЧАЙ НА РУССКОМ.

    {legal_map}

    ПРАВИЛА ОЦЕНКИ:
    - Фин, Опер: шкала 1-8.
    - Юр, Реп, Страт: шкала 1-5.
    - ССЫЛКИ: Запрещено использовать один и тот же закон для всех пунктов. Найди разные источники в базе знаний.

    ДАННЫЕ: Объект: "{name}" ({cat}), Описание: {desc}

    БАЗА ЗНАНИЙ (100 ИСТОЧНИКОВ):
    {context}

    {memory}

    ВЫДАЙ ОТВЕТ СТРОГО ПО ФОРМАТУ (ПИШИ ТОЛЬКО ЭТО):
    ### Этап 1: Правовое обоснование
    [Обоснуй категорию "{cat}", используя статьи из ГК РФ, ФЗ-152, ФЗ-98 или ФЗ-187. Не путай номера законов!].

    ### Этап 2: Покритериальный расчет (Ущерб)
    1. **Фин** (1-8): [Цифра]. Обоснование (TCO, IBM, убытки). Источник: [Имя файла из базы].
    2. **Опер** (1-8): [Цифра]. Обоснование (Непрерывность, ГОСТ 22301). Источник: [Имя файла из базы].
    3. **Юр** (1-5): [Цифра]. Обоснование (Штрафы, КоАП, УК РФ). Источник: [Имя файла из базы].
    4. **Реп** (1-5): [Цифра]. Обоснование (Доверие, PR-риски). Источник: [Имя файла из базы].
    5. **Страт** (1-5): [Цифра]. Обоснование (Доктрина ИБ РФ, Конкуренция). Источник: [Имя файла из базы].
    """

    prompt = ChatPromptTemplate.from_template(template)
    retrieved_docs = retriever.invoke(f"{resource_name} {resource_description}")
    context_text = format_docs(retrieved_docs)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "legal_map": STRICT_LEGAL_MAP, "memory": memory_text, "context": context_text,
        "name": resource_name, "desc": resource_description, "cat": resource_category
    })


def analyze_event_impact(resource_name, last_ranks, event_desc, past_examples=[]):
    """Динамический анализ события по 100 источникам"""
    llm = OllamaLLM(model="deepseek-r1:8b", temperature=0.1, num_ctx=12800)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={'k': 15})

    f_total, r_fin, r_oper, r_jur, r_rep, r_strat = last_ranks
    memory_text = format_learning_context(past_examples)

    template = """
    ИНСТРУКЦИЯ: Пересчитай ранги УЩЕРБА для "{res_name}" после события: "{e_desc}".
    ОТВЕЧАЙ НА РУССКОМ. 

    {legal_map}

    ТЕКУЩИЕ РАНГИ: Фин:{r_fin}, Опер:{r_oper}, Юр:{r_jur}, Реп:{r_rep}, Страт:{r_strat}.

    ЗАКОН ИЗМЕНЕНИЯ:
    - Негативное событие (утечка, атака) -> Цифра ВВЕРХ. (Был 3 -> стал 4 или 5).
    - Положительное (архив, патч) -> Цифра ВНИЗ.
    - Лимиты: Юр/Реп/Страт не выше 5! Фин/Опер не выше 8!

    БАЗА ЗНАНИЙ ДЛЯ ОБОСНОВАНИЯ (100 ИСТОЧНИКОВ):
    {context}

    {memory}

    ВЫПОЛНИ АНАЛИЗ ПО ФОРМЕ:
    ### Этап 1: Характер влияния
    ### Этап 2: Новые значения
    - **Фин**: был {r_fin} -> станет [X]. Обоснование. Источник: [Имя файла из базы].
    - **Опер**: был {r_oper} -> станет [X]. Обоснование. Источник: [Имя файла из базы].
    - **Юр**: был {r_jur} -> станет [X]. Обоснование. Источник: [Имя файла из базы].
    - **Реп**: был {r_rep} -> станет [X]. Обоснование. Источник: [Имя файла из базы].
    - **Страт**: был {r_strat} -> станет [X]. Обоснование. Источник: [Имя файла из базы].
    """

    retrieved_docs = retriever.invoke(event_desc)
    context_text = format_docs(retrieved_docs)
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "legal_map": STRICT_LEGAL_MAP, "context": context_text, "res_name": resource_name,
        "memory": memory_text, "r_fin": r_fin, "r_oper": r_oper, "r_jur": r_jur,
        "r_rep": r_rep, "r_strat": r_strat, "e_desc": event_desc
    })