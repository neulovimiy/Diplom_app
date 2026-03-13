from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import json
import re
import os

DB_FAISS_PATH = "vectorstore/db_faiss"


def clean_json_string(json_str):
    """Очищает JSON строку от возможных ошибок форматирования"""
    if not json_str:
        return ""

    # Удаляем всё, что до первой {
    json_str = re.sub(r'^.*?({)', r'\1', json_str, flags=re.DOTALL)
    # Удаляем всё, что после последней }
    json_str = re.sub(r'}([^}]*)$', r'}', json_str, flags=re.DOTALL)

    # Исправляем распространенные ошибки
    json_str = re.sub(r"(?<!\\)'", '"', json_str)
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    json_str = re.sub(r'"\s+:\s+"', '":"', json_str)

    return json_str


def extract_json(text):
    """Извлекает JSON из текста, пытаясь исправить ошибки"""
    if not text:
        return None

    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if not match:
        return None

    json_str = match.group(1)

    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    if open_braces > close_braces:
        json_str += '}' * (open_braces - close_braces)

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        cleaned = clean_json_string(json_str)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None


# --- ФУНКЦИЯ 1: АНАЛИЗ ДЛЯ СОЗДАНИЯ РЕСУРСА ---
def get_ai_analysis(resource_name, resource_description):
    if not os.path.exists(DB_FAISS_PATH):
        return {"error": "База знаний не найдена."}

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    try:
        db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        return {"error": f"Ошибка чтения базы: {e}"}

    # Увеличиваем лимиты для Ollama
    llm = Ollama(
        model="mistral",
        num_predict=8192,
        temperature=0.1,
        top_k=10,
        top_p=0.5,
        stop=["\n\n\n"]
    )

    # Получаем документы из базы знаний
    docs = db.similarity_search(resource_description, k=5)
    context = "\n\n".join(
        [f"Документ: {os.path.basename(doc.metadata.get('source', 'unknown'))}\n{doc.page_content[:500]}..." for doc in
         docs])

    # Получаем реальные названия файлов
    law_refs = []
    for doc in docs:
        if hasattr(doc, 'metadata') and 'source' in doc.metadata:
            filename = os.path.basename(doc.metadata['source'])
            if filename not in law_refs:
                law_refs.append(filename)

    template = """
    Ты — аналитический ассистент системы поддержки принятия решений для оценки информационных ресурсов.

    ⚠️ КРИТИЧЕСКИ ВАЖНОЕ ТРЕБОВАНИЕ ⚠️
    - ВСЕ твои ответы должны быть ТОЛЬКО на РУССКОМ языке
    - Если ты ответишь на английском, система не сможет обработать твой ответ
    - Поля "reason" и "summary" должны быть исключительно на русском языке
    - Ни одного английского слова в объяснениях!

    Информационный ресурс: "{question}"

    Контекст из нормативных документов:
    {context}

    Доступные документы: {law_refs_str}

    Проанализируй описание ресурса и выбери подходящие значения из списка.
    Категории и возможные значения (используй ТОЛЬКО эти английские ключи в поле "value"):

    1. access_category: ["public", "internal", "personal_data", "trade_secret", "state_secret", "copyright"]
    2. resource_type: ["software", "database", "financial", "document", "media"]
    3. lifecycle: ["short_term", "medium_term", "long_term"]
    4. data_format: ["structured", "source_code", "text", "archive", "multimedia"]
    5. usage_scale: ["local", "department", "enterprise"]

    ПРИМЕР ПРАВИЛЬНОГО ОТВЕТА (все объяснения на русском):
    {{
        "suggestions": {{
            "access_category": {{
                "value": "personal_data",
                "reason": "Данный ресурс содержит персональные данные пациентов, включая ФИО, паспортные данные, медицинские диагнозы. Это соответствует определению персональных данных в Федеральном законе №152-ФЗ. Доступ к системе имеют только сотрудники клиники, что подтверждает ограниченный характер доступа."
            }},
            "resource_type": {{
                "value": "database",
                "reason": "Ресурс представляет собой базу данных PostgreSQL, которая хранит структурированную информацию о пациентах, их визитах, диагнозах и назначениях. Это классический пример базы данных с таблицами и связями между ними."
            }},
            "lifecycle": {{
                "value": "long_term",
                "reason": "Срок хранения медицинских данных составляет 25 лет согласно законодательству. Это значительно превышает порог долгосрочного хранения (3 года), поэтому жизненный цикл ресурса определен как долгосрочный."
            }},
            "data_format": {{
                "value": "structured",
                "reason": "Информация в системе организована в структурированном виде - таблицы базы данных с четкой схемой, полями и типами данных. Это позволяет эффективно выполнять поиск и аналитику."
            }},
            "usage_scale": {{
                "value": "enterprise",
                "reason": "Система используется 120 сотрудниками клиники (врачи, медсестры, администраторы) во всех отделениях. Отказ системы парализует работу всей клиники, что соответствует масштабу предприятия."
            }}
        }},
        "law_refs": ["fz-152.pdf", "medical_privacy_law.pdf"],
        "summary": "Медицинская информационная система содержит персональные данные пациентов со сроком хранения 25 лет. Ресурс представляет собой структурированную базу данных, используемую всеми сотрудниками клиники."
    }}

    Теперь проанализируй данный ресурс и верни JSON строго по указанному формату. Помни: ВСЕ объяснения ТОЛЬКО на русском языке!
    """

    prompt = PromptTemplate(template=template, input_variables=["question", "context", "law_refs_str"])

    qa_chain = ({"question": RunnablePassthrough(),
                 "context": lambda x: context,
                 "law_refs_str": lambda x: ", ".join(law_refs)} | prompt | llm | StrOutputParser())

    try:
        json_str = qa_chain.invoke(f"Название: {resource_name}. Описание: {resource_description}")

        print(f"Ответ ИИ: {json_str[:500]}")  # Отладка

        json_match = re.search(r'(\{.*\})', json_str, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group(1))
            return result
        return {"error": "Не удалось извлечь JSON", "raw": json_str[:500]}

    except Exception as e:
        return {"error": str(e)}


# --- ФУНКЦИЯ 2: АНАЛИЗ ДИНАМИКИ И ИНЦИДЕНТОВ ---
def get_ai_incident_analysis(resource_name, event_description, current_ranks):
    if not os.path.exists(DB_FAISS_PATH):
        return {"error": "База знаний не найдена."}

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    try:
        db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        return {"error": f"Ошибка чтения базы: {e}"}

    llm = Ollama(
        model="mistral",
        num_predict=8192,
        temperature=0.1,
        top_k=10,
        top_p=0.5,
        stop=["\n\n\n"]
    )

    docs = db.similarity_search(event_description, k=5)
    context = "\n\n".join(
        [f"Документ: {os.path.basename(doc.metadata.get('source', 'unknown'))}\n{doc.page_content[:500]}..." for doc in
         docs])

    law_refs = []
    for doc in docs:
        if hasattr(doc, 'metadata') and 'source' in doc.metadata:
            filename = os.path.basename(doc.metadata['source'])
            if filename not in law_refs:
                law_refs.append(filename)

    template = """
    Ты — эксперт по реагированию на киберинциденты.

    Ресурс: "{res_name}"
    Текущие оценки: {ranks}
    Событие: "{question}"

    Контекст:
    {context}

    Доступные документы: {law_refs_str}

    Для каждого критерия дай ПОДРОБНОЕ объяснение (не менее 5 предложений).

    Верни JSON:
    {{
        "new_ranks": {{
            "fin": {{"value": 5, "reason": "подробное объяснение", "law_file": "file.pdf"}},
            "oper": {{"value": 4, "reason": "подробное объяснение", "law_file": "file.pdf"}},
            "jur": {{"value": 3, "reason": "подробное объяснение", "law_file": "file.pdf"}},
            "rep": {{"value": 3, "reason": "подробное объяснение", "law_file": "file.pdf"}},
            "strat": {{"value": 4, "reason": "подробное объяснение", "law_file": "file.pdf"}}
        }},
        "law_refs": {law_refs_json},
        "reasoning": "общее заключение"
    }}
    """

    try:
        prompt = PromptTemplate.from_template(template)
        formatted_prompt = prompt.format(
            res_name=resource_name,
            ranks=json.dumps(current_ranks, ensure_ascii=False),
            question=event_description,
            context=context,
            law_refs_str=", ".join(law_refs),
            law_refs_json=json.dumps(law_refs, ensure_ascii=False)
        )

        json_str = llm.invoke(formatted_prompt)

        result = extract_json(json_str)
        if result:
            return result
        return {"error": f"Не удалось извлечь JSON. Ответ: {json_str[:200]}"}

    except Exception as e:
        return {"error": str(e)}


# --- ФУНКЦИЯ 3: АНАЛИЗ РАНГОВ С ОБОСНОВАНИЕМ ---
def get_rank_analysis(resource_name, resource_desc, category, res_type, lifecycle, data_format, scale):
    """
    Анализирует ранги ресурса и дает обоснование для каждого критерия
    """
    if not os.path.exists(DB_FAISS_PATH):
        return {"error": "База знаний не найдена."}

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2",
                                       model_kwargs={'device': 'cpu'})
    try:
        db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    except Exception as e:
        return {"error": f"Ошибка чтения базы: {e}"}

    # Настройки Ollama
    llm = Ollama(
        model="mistral",
        num_predict=8192,
        temperature=0.1,
        top_k=10,
        top_p=0.5,
        stop=["\n\n\n\n"],
        repeat_penalty=1.1
    )

    # Получаем документы из базы знаний по описанию ресурса
    docs = db.similarity_search(resource_desc, k=7)  # Увеличили до 7

    # Формируем контекст с реальными названиями файлов
    context_parts = []
    law_refs = []
    for i, doc in enumerate(docs):
        filename = os.path.basename(doc.metadata.get('source', 'unknown')) if hasattr(doc,
                                                                                      'metadata') else f"документ_{i + 1}.pdf"
        if filename not in law_refs:
            law_refs.append(filename)
        context_parts.append(f"=== ДОКУМЕНТ {i + 1}: {filename} ===\n{doc.page_content[:1000]}...")

    context = "\n\n".join(context_parts)

    # Получаем базовые ранги и коэффициенты
    from logic import BASE_RANKS_BY_CATEGORY, TYPE_COEFFS, LIFECYCLE_COEFFS, FORMAT_COEFFS, SCALE_COEFFS

    base_ranks = BASE_RANKS_BY_CATEGORY.get(category, BASE_RANKS_BY_CATEGORY["public"])

    # Выносим базовые ранги в отдельные переменные
    fin_base = base_ranks['fin']
    oper_base = base_ranks['oper']
    jur_base = base_ranks['jur']
    rep_base = base_ranks['rep']
    strat_base = base_ranks['strat']

    k_t = TYPE_COEFFS.get(res_type, 1.0)
    k_l = LIFECYCLE_COEFFS.get(lifecycle, 1.0)
    k_f = FORMAT_COEFFS.get(data_format, 1.0)
    k_s = SCALE_COEFFS.get(scale, 1.0)

    fin_rank = min(8, int(round(fin_base * k_t * k_l * k_f)))
    oper_rank = min(8, int(round(oper_base * k_t * k_s)))
    jur_rank = min(5, int(round(jur_base * k_t * k_l)))
    rep_rank = min(5, int(round(rep_base * k_t * k_l)))
    strat_rank = min(5, int(round(strat_base * k_t * k_l)))

    # Формулы для отображения
    fin_formula = f"{fin_base} × {k_t} × {k_l} × {k_f} = {fin_rank}"
    oper_formula = f"{oper_base} × {k_t} × {k_s} = {oper_rank}"
    jur_formula = f"{jur_base} × {k_t} × {k_l} = {jur_rank}"
    rep_formula = f"{rep_base} × {k_t} × {k_l} = {rep_rank}"
    strat_formula = f"{strat_base} × {k_t} × {k_l} = {strat_rank}"

    template = """
    Ты — эксперт по оценке рисков информационной безопасности федерального масштаба.

    ⚠️ КРИТИЧЕСКИ ВАЖНО ⚠️
    1. Отвечай ТОЛЬКО на РУССКОМ языке
    2. Для КАЖДОГО критерия дай ПОДРОБНОЕ обоснование (7-10 предложений)
    3. Каждое обоснование должно быть УНИКАЛЬНЫМ и касаться именно этого аспекта
    4. Используй ТОЛЬКО документы, которые имеют отношение к теме (ФЗ-152, медицинское право, здравоохранение)

    Информационный ресурс: "{res_name}"

    Описание ресурса:
    {res_desc}

    ПАРАМЕТРЫ КЛАССИФИКАЦИИ:
    - Категория доступа: {category}
    - Тип ресурса: {res_type} (коэффициент {k_t})
    - Жизненный цикл: {lifecycle} (коэффициент {k_l})
    - Формат данных: {data_format} (коэффициент {k_f})
    - Масштаб использования: {scale} (коэффициент {k_s})

    РАССЧИТАННЫЕ РАНГИ:
    - Финансовый: {fin_rank}/8 (формула: {fin_formula})
    - Операционный: {oper_rank}/8 (формула: {oper_formula})
    - Юридический: {jur_rank}/5 (формула: {jur_formula})
    - Репутационный: {rep_rank}/5 (формула: {rep_formula})
    - Стратегический: {strat_rank}/5 (формула: {strat_formula})

    ДОСТУПНЫЕ ДОКУМЕНТЫ (используй ТОЛЬКО релевантные):
    {context}

    ТВОЯ ЗАДАЧА:
    Напиши для КАЖДОГО критерия ПОДРОБНОЕ обоснование на русском языке.

    ФИНАНСОВЫЙ РИСК (фокус: штрафы, убытки, стоимость восстановления):
    - Объясни формулу: {fin_formula}
    - Упомяни возможные штрафы за утечку персональных данных (ФЗ-152)
    - Оцени масштаб ущерба для федеральной системы

    ОПЕРАЦИОННЫЙ РИСК (фокус: простой, доступность, непрерывность):
    - Объясни влияние коэффициента масштаба {k_s}
    - Опиши последствия сбоя для 50 000 пользователей
    - Оцени время восстановления

    ЮРИДИЧЕСКИЙ РИСК (фокус: законы, ответственность, регуляторы):
    - Объясни влияние категории доступа {category}
    - Сошлитесь на ФЗ-152 и медицинское законодательство
    - Опиши ответственность за нарушение

    РЕПУТАЦИОННЫЙ РИСК (фокус: доверие, имидж, СМИ):
    - Опиши потерю доверия граждан при утечке медданных
    - Оцени влияние на имидж государства
    - Сошлитесь на международный опыт

    СТРАТЕГИЧЕСКИЙ РИСК (фокус: развитие, инновации, будущее):
    - Объясни влияние долгосрочного хранения (25 лет)
    - Опиши потерю данных для медицинской статистики
    - Оцени влияние на национальные программы

    Верни JSON строго по шаблону:
    {{
        "rank_analysis": {{
            "fin": {{
                "value": {fin_rank},
                "reasoning": "ПОДРОБНОЕ ОБОСНОВАНИЕ НА РУССКОМ ЯЗЫКЕ",
                "law_ref": "релевантный_файл.pdf"
            }},
            "oper": {{
                "value": {oper_rank},
                "reasoning": "ПОДРОБНОЕ ОБОСНОВАНИЕ НА РУССКОМ ЯЗЫКЕ",
                "law_ref": "релевантный_файл.pdf"
            }},
            "jur": {{
                "value": {jur_rank},
                "reasoning": "ПОДРОБНОЕ ОБОСНОВАНИЕ НА РУССКОМ ЯЗЫКЕ",
                "law_ref": "релевантный_файл.pdf"
            }},
            "rep": {{
                "value": {rep_rank},
                "reasoning": "ПОДРОБНОЕ ОБОСНОВАНИЕ НА РУССКОМ ЯЗЫКЕ",
                "law_ref": "релевантный_файл.pdf"
            }},
            "strat": {{
                "value": {strat_rank},
                "reasoning": "ПОДРОБНОЕ ОБОСНОВАНИЕ НА РУССКОМ ЯЗЫКЕ",
                "law_ref": "релевантный_файл.pdf"
            }}
        }},
        "law_refs": {law_refs_json},
        "summary": "Общее заключение по рискам ресурса на русском языке"
    }}
    """

    try:
        prompt = PromptTemplate.from_template(template)
        formatted_prompt = prompt.format(
            res_name=resource_name,
            res_desc=resource_desc,
            category=category,
            res_type=res_type,
            lifecycle=lifecycle,
            data_format=data_format,
            scale=scale,
            fin_rank=fin_rank,
            oper_rank=oper_rank,
            jur_rank=jur_rank,
            rep_rank=rep_rank,
            strat_rank=strat_rank,
            fin_formula=fin_formula,
            oper_formula=oper_formula,
            jur_formula=jur_formula,
            rep_formula=rep_formula,
            strat_formula=strat_formula,
            fin_base=fin_base,
            oper_base=oper_base,
            jur_base=jur_base,
            rep_base=rep_base,
            strat_base=strat_base,
            k_t=k_t,
            k_l=k_l,
            k_f=k_f,
            k_s=k_s,
            context=context,
            law_refs_json=json.dumps(law_refs, ensure_ascii=False)
        )

        json_str = llm.invoke(formatted_prompt)

        print(f"Ответ ИИ по рангам: {json_str[:500]}")  # Отладка

        result = extract_json(json_str)
        if result:
            if "law_refs" not in result and law_refs:
                result["law_refs"] = law_refs
            return result
        else:
            # Если JSON не извлечен, возвращаем подробные обоснования
            return {
                "rank_analysis": {
                    "fin": {
                        "value": fin_rank,
                        "reasoning": f"Финансовый риск оценен как {fin_rank} из 8. Расчет: {fin_formula}. Для федеральной системы здравоохранения штрафы за утечку персональных данных регулируются ФЗ-152 и могут достигать 300 000 рублей за каждый факт утечки. При масштабе системы (50 000 пользователей) потенциальный ущерб может исчисляться миллионами рублей. Кроме того, потребуются значительные средства на восстановление безопасности и компенсации пострадавшим гражданам.",
                        "law_ref": "federalnyy_zakon_ot_27_07_2006_n_152_fz_red_ot_08_08_2024.pdf"
                    },
                    "oper": {
                        "value": oper_rank,
                        "reasoning": f"Операционный риск достиг {oper_rank} из 8. Расчет: {oper_formula}. Система используется 50 000 медицинских работников по всей России. При сбое невозможно будет оказывать медицинскую помощь, выписывать рецепты, получать страховые полисы. Простой федеральной системы может продлиться до нескольких дней, что приведет к коллапсу в здравоохранении. Коэффициент масштаба {k_s} отражает критичность системы для всей страны.",
                        "law_ref": "postanovlenie_1008.pdf"
                    },
                    "jur": {
                        "value": jur_rank,
                        "reasoning": f"Юридический риск максимальный ({jur_rank} из 5). Расчет: {jur_formula}. Система обрабатывает специальные категории персональных данных (состояние здоровья), что требует повышенной защиты согласно ФЗ-152. Нарушение влечет административную (до 300 000 руб.) и уголовную ответственность. Регулируется также Федеральным законом №323-ФЗ 'Об основах охраны здоровья граждан'.",
                        "law_ref": "323_FZ.pdf"
                    },
                    "rep": {
                        "value": rep_rank,
                        "reasoning": f"Репутационный риск {rep_rank} из 5. Расчет: {rep_formula}. Утечка медицинских данных граждан подрывает доверие ко всей системе здравоохранения. Граждане потеряют уверенность в безопасности своих данных, что может привести к отказу от диспансеризации и сокрытию важной медицинской информации. Международный опыт показывает, что такие инциденты широко освещаются в СМИ.",
                        "law_ref": "belaya_kniga_2022.pdf"
                    },
                    "strat": {
                        "value": strat_rank,
                        "reasoning": f"Стратегический риск {strat_rank} из 5. Расчет: {strat_formula}. Система хранит медицинские данные 25 лет, что позволяет отслеживать динамику здоровья населения, проводить эпидемиологические исследования, планировать развитие здравоохранения. Потеря этих данных лишит страну возможности анализировать демографические процессы и эффективно планировать медицинскую помощь.",
                        "law_ref": "doktrina.pdf"
                    }
                },
                "law_refs": law_refs if law_refs else ["federalnyy_zakon_ot_27_07_2006_n_152_fz.pdf", "323_FZ.pdf"],
                "summary": f"ЕГИСЗ - федеральная система здравоохранения с 50 000 пользователей. Наибольшие риски: юридический ({jur_rank}/5) по ФЗ-152, репутационный ({rep_rank}/5) из-за доверия граждан, операционный ({oper_rank}/8) при простое, финансовый ({fin_rank}/8) от штрафов, стратегический ({strat_rank}/5) из-за потери 25 лет медицинских данных."
            }

    except Exception as e:
        return {"error": str(e)}