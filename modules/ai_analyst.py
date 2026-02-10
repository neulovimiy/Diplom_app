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
    """Извлекает текст и метаданные для цитирования"""
    formatted = []
    for doc in docs:
        source = os.path.basename(doc.metadata.get('source', 'Источник'))
        page = doc.metadata.get('page', '?')
        content = doc.page_content.replace('\n', ' ').strip()
        formatted.append(f"📖 [ФАЙЛ: {source} | СТР: {page}]: {content}")
    return "\n\n".join(formatted)


def format_learning_context(examples):
    """Форматирует прошлый опыт для обучения ИИ"""
    if not examples: return "Это первая оценка в системе."
    formatted = "ТВОЙ ПРЕДЫДУЩИЙ ОПЫТ (используй для логики):\n"
    for ex in examples:
        formatted += f"- Ресурс: {ex[0]} | Событие: {ex[6]} | Итог: {ex[7]} [Ф:{ex[1]}, О:{ex[2]}, Ю:{ex[3]}, Р:{ex[4]}, С:{ex[5]}]\n"
    return formatted


def get_ai_recommendation(resource_name, resource_description, resource_category, past_examples=[]):
    """ПЕРВИЧНАЯ ЭКСПЕРТИЗА (Шаг 1)"""
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={'k': 12})
    llm = OllamaLLM(model="mistral", temperature=0.1)

    memory_text = format_learning_context(past_examples)

    template = """
    ИНСТРУКЦИЯ ДЛЯ ГЛАВНОГО АУДИТОРА ИБ:
    Тебе нужно оценить УЩЕРБ от потери ресурса. Используй ТОЛЬКО данные из БАЗЫ ЗНАНИЙ (50 источников).

    ШКАЛЫ (СТРОГО):
    1. Фин (Финансы): 1 (нет потерь) - 8 (банкротство).
    2. Опер (Операции): 1 (незаметно) - 8 (полная остановка предприятия).
    3. Юр (Юридический): 1 (нет санкций) - 5 (уголовная ответственность/отзыв лицензии).
    4. Реп (Репутация): 1 (нет влияния) - 5 (федеральный скандал).
    5. Страт (Стратегия): 1 (нет влияния) - 5 (утеря технологий/закрытие проекта).

    ОБЪЕКТ: "{name}"
    ОПИСАНИЕ: {desc}
    КАТЕГОРИЯ: "{cat}"

    {memory}

    КОНТЕКСТ ИЗ БАЗЫ ЗНАНИЙ:
    {context}

    ЗАДАНИЕ:
    Выдай отчет строго по шаблону ниже. Не пиши вступлений типа "Как эксперт...". Сразу к делу.

    ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:
    ### Этап 1: Правовое обоснование режима
    Объект содержит [факты из описания]. Согласно ФЗ-152 (стр. 5) и Постановлению №1119 (стр. 2), это ПДн 1-го уровня.
    ### Этап 2: Покритериальный расчет
    - **Фин** (1-8): 7. Обоснование: Согласно отчету IBM (стр. 2), стоимость записи в медицине 170$. При 500к записей ущерб критический.
    - **Опер** (1-8): 8. Обоснование: Согласно ГОСТ 22301 (стр. 12), простой более 4 часов ведет к необратимым потерям.

    ТВОЙ ОТВЕТ (заполни для объекта "{name}"):
    """
    prompt = ChatPromptTemplate.from_template(template)
    retrieved_docs = retriever.invoke(resource_name + " " + resource_description)
    context_text = format_docs(retrieved_docs)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(
        {"memory": memory_text, "context": context_text, "name": resource_name, "desc": resource_description,
         "cat": resource_category})


def analyze_event_impact(resource_name, last_ranks, event_desc, past_examples=[]):
    """ДИНАМИЧЕСКИЙ АНАЛИЗ (Шаг 2)"""
    llm = OllamaLLM(model="mistral", temperature=0.1)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever(search_kwargs={'k': 12})

    f_total, r_fin, r_oper, r_jur, r_rep, r_strat = last_ranks
    memory_text = format_learning_context(past_examples)

    template = """
    ИНСТРУКЦИЯ ДЛЯ РИСК-МЕНЕДЖЕРА:
    Проанализируй событие "{e_desc}" для ресурса "{res_name}".

    ТЕКУЩИЕ РАНГИ (Твоя точка старта): 
    Фин:{r_fin}, Опер:{r_oper}, Юр:{r_jur}, Реп:{r_rep}, Страт:{r_strat}.

    МАТЕМАТИЧЕСКИЕ ПРАВИЛА (ОБЯЗАТЕЛЬНО):
    1. Направление: 
       - Событие ПЛОХОЕ (Взлом, Утечка, Уязвимость) -> Новое число ДОЛЖНО БЫТЬ БОЛЬШЕ текущего.
       - Событие ХОРОШЕЕ (Патч, Резерв, Устаревание) -> Новое число ДОЛЖНО БЫТЬ МЕНЬШЕ текущего.
    2. Обоснование: Ссылка на конкретный файл и страницу из базы знаний ОБЯЗАТЕЛЬНА для каждого пункта.

    {memory}

    БАЗА ЗНАНИЙ ДЛЯ ЦИТИРОВАНИЯ:
    {context}

    ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА:
    ### Этап 1: Характер влияния
    Событие является критической угрозой. Ущерб растет из-за нарушения конфиденциальности.
    ### Этап 2: Новые значения критериев
    - **Фин**: был 5 -> станет 7. Обоснование: Рост затрат на суды. Источник: IBM_Report.pdf, Стр 10.
    - **Юр**: был 3 -> станет 5. Обоснование: Нарушение ст. 13.11 КоАП. Источник: KoAP_RF.pdf, Стр 45.

    ТВОЙ ОТВЕТ (заполни для события "{e_desc}"):
    """
    retrieved_docs = retriever.invoke(event_desc)
    context_text = format_docs(retrieved_docs)
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke(
        {"memory": memory_text, "context": context_text, "res_name": resource_name, "r_fin": r_fin, "r_oper": r_oper,
         "r_jur": r_jur, "r_rep": r_rep, "r_strat": r_strat, "e_desc": event_desc})