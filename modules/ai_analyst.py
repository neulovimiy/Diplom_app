from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import json
import re
import os
from typing import Dict, List, Any

DB_FAISS_PATH = "vectorstore/db_faiss"

# Словари для перевода (это эталонные значения)
ACCESS_CATEGORIES = {
    "public": "📢 Общедоступная",
    "internal": "🏢 Внутренняя (ДСП)",
    "personal_data": "👤 Персональные данные (ПДн)",
    "trade_secret": "🔒 Коммерческая тайна (КТ)",
    "state_secret": "⚡ Государственная тайна",
    "copyright": "© Интеллектуальная собственность"
}

RESOURCE_TYPES = {
    "unknown": "❓ Неизвестно",
    "software": "💻 Программное обеспечение",
    "database": "🗄️ База данных",
    "financial": "💰 Финансовая отчетность",
    "document": "📄 Текстовая документация",
    "config": "⚙️ Конфигурационные файлы",
    "media": "🎬 Мультимедиа"
}

LIFECYCLE = {
    "unknown": "❓ Неизвестно",
    "short_term": "⏱️ Краткосрочный (дни/месяцы)",
    "medium_term": "📅 Среднесрочный (до 1 года)",
    "long_term": "📆 Долгосрочный (более 1 года)"
}

FORMAT = {
    "unknown": "❓ Неизвестно",
    "structured": "🗂️ Структурированные (БД/JSON)",
    "source_code": "👨‍💻 Исходный код",
    "text": "📝 Текстовые документы",
    "archive": "📦 Архивы",
    "multimedia": "🎥 Мультимедиа"
}

SCALE = {
    "unknown": "❓ Неизвестно",
    "local": "👤 Локальный",
    "department": "👥 Уровень отдела",
    "enterprise": "🏭 Масштаб предприятия"
}

CONFIDENTIALITY = {
    "unknown": "❓ Неизвестно",
    "open": "🔓 Открытая информация",
    "internal": "🏢 Для внутреннего пользования",
    "confidential": "🔒 Конфиденциально",
    "secret": "⚡ Секретно",
    "top_secret": "🛡️ Особой важности"
}

USERS_COUNT = {
    "unknown": "❓ Неизвестно",
    "1-10": "👤 1-10 пользователей",
    "11-100": "👥 11-100 пользователей",
    "101-1000": "👥👥 101-1000 пользователей",
    "1001-10000": "🏢 1001-10000 пользователей",
    "10000+": "🌐 Более 10000 пользователей"
}

CRITICALITY = {
    "unknown": "❓ Неизвестно",
    "low": "🟢 Низкая",
    "medium": "🟡 Средняя",
    "high": "🟠 Высокая",
    "critical": "🔴 Критическая"
}

BACKUP = {
    "unknown": "❓ Неизвестно",
    "daily": "✅ Ежедневный",
    "weekly": "📅 Еженедельный",
    "monthly": "📆 Ежемесячный",
    "none": "❌ Отсутствует"
}


def clean_json_string(json_str):
    json_str = re.sub(r'^.*?({)', r'\1', json_str, flags=re.DOTALL)
    json_str = re.sub(r'}([^}]*)$', r'}', json_str, flags=re.DOTALL)
    return json_str


def extract_json(text):
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            return json.loads(clean_json_string(match.group(1)))
    return None


def get_relevant_documents(query: str, k: int = 10) -> List[Dict]:
    if not os.path.exists(DB_FAISS_PATH):
        return []
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    docs = db.max_marginal_relevance_search(query, k=k, fetch_k=20)
    return [{"filename": d.metadata.get('source', d.metadata.get('source_file', 'unknown')),
             "content": d.page_content} for d in docs]


def suggest_parameters(resource_name: str, resource_desc: str) -> Dict[str, Any]:
    docs = get_relevant_documents(f"{resource_name} {resource_desc}", k=10)
    context = "\n\n".join([f"ФАЙЛ: {d['filename']}\nТЕКСТ: {d['content'][:800]}" for d in docs])

    llm = Ollama(model="rscr/ruadapt_qwen2.5_32b:Q4_K_M", temperature=0.1)  # или deepseek-r1:14b / qwen2.5:14b

    template = """
    Ты — эксперт-аналитик по информационной безопасности. Твоя задача — извлечь факты из описания и строго следовать им.

    Информационный ресурс: "{resource_name}"
    ОПИСАНИЕ:
    {resource_desc}

    Контекст из документов:
    {context}

    Проанализируй описание и выбери значения ТОЛЬКО из указанных списков:

    ДОСТУПНЫЕ ЗНАЧЕНИЯ:

    1. access_category:
       public - Общедоступная
       internal - Внутренняя (ДСП)
       personal_data - Персональные данные (ПДн)
       trade_secret - Коммерческая тайна (КТ)
       state_secret - Государственная тайна
       copyright - Интеллектуальная собственность

    2. resource_type:
       unknown - Неизвестно
       software - Программное обеспечение
       database - База данных
       financial - Финансовая отчетность
       document - Текстовая документация
       config - Конфигурационные файлы
       media - Мультимедиа

    3. lifecycle:
       unknown - Неизвестно
       short_term - Краткосрочный (дни/месяцы)
       medium_term - Среднесрочный (до 1 года)
       long_term - Долгосрочный (более 1 года)

    4. data_format:
       unknown - Неизвестно
       structured - Структурированные (БД/JSON)
       source_code - Исходный код
       text - Текстовые документы
       archive - Архивы
       multimedia - Мультимедиа

    5. usage_scale:
       unknown - Неизвестно
       local - Локальный
       department - Уровень отдела
       enterprise - Масштаб предприятия

    6. confidentiality:
       unknown - Неизвестно
       open - Открытая информация
       internal - Для внутреннего пользования
       confidential - Конфиденциально
       secret - Секретно
       top_secret - Особой важности

    7. users_count:
       unknown - Неизвестно
       1-10 - 1-10 пользователей
       11-100 - 11-100 пользователей
       101-1000 - 101-1000 пользователей
       1001-10000 - 1001-10000 пользователей
       10000+ - Более 10000 пользователей

    8. business_criticality:
       unknown - Неизвестно
       low - Низкая
       medium - Средняя
       high - Высокая
       critical - Критическая

    9. backup:
       unknown - Неизвестно
       daily - Ежедневный
       weekly - Еженедельный
       monthly - Ежемесячный
       none - Отсутствует

    В поле "value" ставь английский ключ (например, "trade_secret", "database").
    В поле "reason" напиши краткое обоснование на русском языке.

    Верни JSON в формате:
    {{
      "suggestions": {{
        "access_category": {{"value": "...", "reason": "..."}},
        "resource_type": {{"value": "...", "reason": "..."}},
        "lifecycle": {{"value": "...", "reason": "..."}},
        "data_format": {{"value": "...", "reason": "..."}},
        "usage_scale": {{"value": "...", "reason": "..."}},
        "confidentiality": {{"value": "...", "reason": "..."}},
        "users_count": {{"value": "...", "reason": "..."}},
        "business_criticality": {{"value": "...", "reason": "..."}},
        "backup": {{"value": "...", "reason": "..."}}
      }},
      "law_refs": [],
      "summary": "Краткое резюме на русском"
    }}
    """

    prompt = PromptTemplate.from_template(template)
    response = llm.invoke(prompt.format(
        resource_name=resource_name,
        resource_desc=resource_desc,
        context=context
    ))

    result = extract_json(response)
    if not result:
        return {"error": "JSON parse error", "raw": response}

    result["law_refs"] = list(set([d['filename'] for d in docs]))
    return result


# === ФУНКЦИЯ 2: ОБЪЯСНЕНИЕ РАСЧЕТА РАНГОВ ===
def explain_calculation(
        resource_name: str,
        resource_desc: str,
        params: Dict[str, str],
        base_ranks: Dict[str, int],
        coefficients: Dict[str, float],
        final_ranks: Dict[str, int]
) -> Dict[str, Any]:
    """
    ИИ объясняет, почему получились такие ранги на основе документов.
    """
    if not os.path.exists(DB_FAISS_PATH):
        return {"error": "База знаний не найдена"}

    query = f"{resource_name} {resource_desc}"
    docs = get_relevant_documents(query, k=10)

    context = "\n\n".join([
        f"ФАЙЛ: {doc['filename']}\nТЕКСТ: {doc['content'][:800]}..."
        for i, doc in enumerate(docs)
    ])

    law_refs = [doc['filename'] for doc in docs]

    llm = Ollama(
        model="rscr/ruadapt_qwen2.5_32b:Q4_K_M",
        temperature=0.1,
        num_predict=4096,
    )

    template = """
    Ты — эксперт по информационной безопасности.

    Проанализируй результаты математического расчета рангов для информационного ресурса и дай подробное объяснение для КАЖДОГО критерия, ссылаясь на нормативные документы.

    Информационный ресурс: "{resource_name}"
    Описание: {resource_desc}

    ПАРАМЕТРЫ РЕСУРСА (выбраны экспертом):
    - Категория доступа: {access_category}
    - Тип ресурса: {resource_type}
    - Жизненный цикл: {lifecycle}
    - Формат данных: {data_format}
    - Масштаб использования: {usage_scale}
    - Конфиденциальность: {confidentiality}
    - Количество пользователей: {users_count}
    - Критичность для бизнеса: {business_criticality}
    - Резервное копирование: {backup}

    РЕЗУЛЬТАТЫ РАСЧЕТА:
    - Финансовый риск: {fin_rank}/10
    - Операционный риск: {oper_rank}/10
    - Юридический риск: {jur_rank}/8
    - Репутационный риск: {rep_rank}/8
    - Стратегический риск: {strat_rank}/8

    Интегральная сумма SΣ = {total_s}
    Итоговый ранг: {final_rank}

    Контекст из нормативных документов (используй для обоснования):
    {context}

    Для КАЖДОГО из пяти критериев напиши подробное объяснение на русском языке:
    - Почему базовый ранг именно такой (свяжи с категорией доступа)
    - Как каждый коэффициент повлиял на итоговое значение
    - Сошлитесь на конкретные документы из контекста
    - Объясни практический смысл (что означает этот риск для предприятия)

    Верни ТОЛЬКО JSON без дополнительного текста в следующем формате:
    {{
      "summary": "Общее резюме по всем рискам (2-3 предложения)",
      "explanations": {{
        "fin": {{
          "text": "подробное объяснение финансового риска...",
          "law_refs": ["название_файла"]
        }},
        "oper": {{
          "text": "подробное объяснение операционного риска...",
          "law_refs": ["название_файла"]
        }},
        "jur": {{
          "text": "подробное объяснение юридического риска...",
          "law_refs": ["название_файла"]
        }},
        "rep": {{
          "text": "подробное объяснение репутационного риска...",
          "law_refs": ["название_файла"]
        }},
        "strat": {{
          "text": "подробное объяснение стратегического риска...",
          "law_refs": ["название_файла"]
        }}
      }},
      "law_refs_all": {law_refs_json}
    }}
    """

    prompt = PromptTemplate.from_template(template)

    try:
        # Получаем русские названия для параметров
        access_ru = ACCESS_CATEGORIES.get(params.get('access_category', 'unknown'), 'Неизвестно')
        type_ru = RESOURCE_TYPES.get(params.get('resource_type', 'unknown'), 'Неизвестно')
        life_ru = LIFECYCLE.get(params.get('lifecycle', 'unknown'), 'Неизвестно')
        format_ru = FORMAT.get(params.get('data_format', 'unknown'), 'Неизвестно')
        scale_ru = SCALE.get(params.get('usage_scale', 'unknown'), 'Неизвестно')
        conf_ru = CONFIDENTIALITY.get(params.get('confidentiality', 'unknown'), 'Неизвестно')
        users_ru = USERS_COUNT.get(params.get('users_count', 'unknown'), 'Неизвестно')
        crit_ru = CRITICALITY.get(params.get('business_criticality', 'unknown'), 'Неизвестно')
        backup_ru = BACKUP.get(params.get('backup', 'unknown'), 'Неизвестно')

        # Вычисляем итоговый ранг
        s_scores, total_s = calculate_normalization_from_ranks(final_ranks)
        final_rank = get_final_rank_from_sum(total_s)

        formatted_prompt = prompt.format(
            resource_name=resource_name,
            resource_desc=resource_desc[:1000],
            access_category=access_ru,
            resource_type=type_ru,
            lifecycle=life_ru,
            data_format=format_ru,
            usage_scale=scale_ru,
            confidentiality=conf_ru,
            users_count=users_ru,
            business_criticality=crit_ru,
            backup=backup_ru,
            fin_rank=final_ranks.get('fin', '?'),
            oper_rank=final_ranks.get('oper', '?'),
            jur_rank=final_ranks.get('jur', '?'),
            rep_rank=final_ranks.get('rep', '?'),
            strat_rank=final_ranks.get('strat', '?'),
            total_s=total_s,
            final_rank=final_rank,
            context=context,
            law_refs_json=json.dumps(law_refs, ensure_ascii=False)
        )

        response = llm.invoke(formatted_prompt)
        result = extract_json(response)

        if result:
            result["law_refs_all"] = law_refs
            return result
        else:
            # Если JSON не распарсился, возвращаем запасной вариант с объяснениями
            return generate_fallback_explanation(
                resource_name, resource_desc, params, final_ranks, law_refs
            )

    except Exception as e:
        print(f"Ошибка в explain_calculation: {e}")
        return generate_fallback_explanation(
            resource_name, resource_desc, params, final_ranks, law_refs
        )


def generate_fallback_explanation(resource_name, resource_desc, params, final_ranks, law_refs):
    """Генерирует запасное объяснение, если ИИ не сработал"""

    access_ru = ACCESS_CATEGORIES.get(params.get('access_category', 'unknown'), 'Неизвестно')

    explanations = {
        'fin': {
            'text': f"Финансовый риск оценен в {final_ranks.get('fin', '?')}/10. Это значение получено на основе категории доступа '{access_ru}' и параметров ресурса. Для более детального анализа обратитесь к нормативным документам.",
            'law_refs': law_refs[:2]
        },
        'oper': {
            'text': f"Операционный риск оценен в {final_ranks.get('oper', '?')}/10. Данная оценка учитывает влияние на бизнес-процессы и доступность ресурса.",
            'law_refs': law_refs[:2]
        },
        'jur': {
            'text': f"Юридический риск оценен в {final_ranks.get('jur', '?')}/8. Оценка основана на требованиях законодательства к защите информации.",
            'law_refs': law_refs[:2]
        },
        'rep': {
            'text': f"Репутационный риск оценен в {final_ranks.get('rep', '?')}/8. Учитывается потенциальное влияние на имидж компании.",
            'law_refs': law_refs[:2]
        },
        'strat': {
            'text': f"Стратегический риск оценен в {final_ranks.get('strat', '?')}/8. Оценка отражает влияние на долгосрочное развитие.",
            'law_refs': law_refs[:2]
        }
    }

    return {
        "summary": f"Ресурс '{resource_name}' имеет следующие риски: финансовый {final_ranks.get('fin', '?')}/10, операционный {final_ranks.get('oper', '?')}/10, юридический {final_ranks.get('jur', '?')}/8, репутационный {final_ranks.get('rep', '?')}/8, стратегический {final_ranks.get('strat', '?')}/8.",
        "explanations": explanations,
        "law_refs_all": law_refs
    }


# Вспомогательные функции для расчета (добавьте их в конец файла)
def calculate_normalization_from_ranks(ranks):
    """Вычисляет нормализацию из рангов"""
    from logic import MAX_RANKS
    total = 0
    for key, val in ranks.items():
        max_r = MAX_RANKS.get(key, 8)
        if max_r > 1:
            total += (val - 1) / (max_r - 1)
    return None, round(total, 3)


def get_final_rank_from_sum(sum_s):
    """Определяет итоговый ранг по сумме"""
    if sum_s <= 0.55:
        return 1
    elif sum_s <= 1.11:
        return 2
    elif sum_s <= 1.67:
        return 3
    elif sum_s <= 2.22:
        return 4
    elif sum_s <= 2.78:
        return 5
    elif sum_s <= 3.33:
        return 6
    elif sum_s <= 3.89:
        return 7
    elif sum_s <= 4.44:
        return 8
    else:
        return 9

# === ФУНКЦИЯ 3: АНАЛИЗ ИНИЦИИРУЮЩЕГО СОБЫТИЯ ===
def analyze_incident(
        resource_name: str,
        resource_desc: str,
        current_params: Dict[str, str],
        incident_description: str
) -> Dict[str, Any]:
    """
    ИИ анализирует, как инцидент может повлиять на параметры ресурса.
    """
    if not os.path.exists(DB_FAISS_PATH):
        return {"error": "База знаний не найдена"}

    query = f"{incident_description} {resource_name} {resource_desc}"
    docs = get_relevant_documents(query, k=5)

    context = "\n\n".join([
        f"Документ {i + 1}: {doc['filename']}\n{doc['content']}"
        for i, doc in enumerate(docs)
    ])

    llm = Ollama(
        model="rscr/ruadapt_qwen2.5_32b:Q4_K_M",
        num_predict=4096,
        temperature=0.1,
    )

    template = """
    Проанализируй влияние инцидента на параметры ресурса.

    Ресурс: {resource_name}
    Событие: {incident}

    Дай рекомендации по изменению параметров.
    """

    prompt = PromptTemplate.from_template(template)

    try:
        formatted_prompt = prompt.format(
            resource_name=resource_name,
            incident=incident_description,
            context=context
        )

        response = llm.invoke(formatted_prompt)
        return {"analysis": response[:1000]}

    except Exception as e:
        return {"error": str(e)}


# === ФУНКЦИЯ 4: РЕКОМЕНДАЦИИ ПО РАНГАМ ===
# ВАЖНО: Эта функция должна быть на том же уровне отступа, что и другие функции (без отступа внутри другой функции)
# === ФУНКЦИЯ 4: РЕКОМЕНДАЦИИ ПО РАНГАМ ===
def suggest_ranks(resource_name: str, resource_desc: str, params: Dict[str, str]) -> Dict[str, Any]:
    """
    ИИ рекомендует ранги для каждого критерия на основе описания ресурса.
    """
    if not os.path.exists(DB_FAISS_PATH):
        return {"error": "База знаний не найдена"}

    query = f"{resource_name} {resource_desc}"
    docs = get_relevant_documents(query, k=10)

    context = "\n\n".join([
        f"ФАЙЛ: {doc['filename']}\nТЕКСТ: {doc['content'][:800]}..."
        for i, doc in enumerate(docs)
    ])

    llm = Ollama(model="rscr/ruadapt_qwen2.5_32b:Q4_K_M", temperature=0.1)

    template = """
    Ты — эксперт по информационной безопасности.

    Проанализируй описание ресурса и порекомендуй значения рангов для каждого критерия риска, ссылаясь на нормативные документы.

    ВАЖНО: Это предварительные рекомендации. Итоговые ранги будут умножены на коэффициенты, поэтому рекомендованные значения должны быть УМЕРЕННЫМИ (в диапазоне 1-7 для финансового и операционного, 1-6 для остальных).

    Информационный ресурс: "{resource_name}"
    Описание: {resource_desc}

    ПАРАМЕТРЫ РЕСУРСА (уже определены экспертом):
    - Категория доступа: {access_category}
    - Тип ресурса: {resource_type}
    - Жизненный цикл: {lifecycle}
    - Формат данных: {data_format}
    - Масштаб использования: {usage_scale}
    - Конфиденциальность: {confidentiality}
    - Количество пользователей: {users_count}
    - Критичность для бизнеса: {business_criticality}
    - Резервное копирование: {backup}

    Контекст из нормативных документов (используй для обоснования):
    {context}

    На основе описания и документов, порекомендуй значения для каждого критерия риска:

    - Финансовый риск (1-10): оценивает потенциальные денежные потери от утечки, штрафов, судебных исков
    - Операционный риск (1-10): оценивает влияние на бизнес-процессы, простои, остановку работы
    - Юридический риск (1-8): оценивает юридические последствия, ответственность по законам
    - Репутационный риск (1-8): оценивает влияние на репутацию, доверие клиентов
    - Стратегический риск (1-8): оценивает влияние на долгосрочное развитие, конкурентоспособность

    Для каждого критерия дай:
    - value: число от 1 до максимального значения (НО ПОМНИ, что это только предварительная оценка)
    - reason: подробное обоснование на русском языке (3-5 предложений) со ссылкой на документы

    Верни JSON в формате:
    {{
      "ranks": {{
        "fin": {{"value": 5, "reason": "подробное обоснование финансового риска с ссылкой на документы..."}},
        "oper": {{"value": 4, "reason": "подробное обоснование операционного риска с ссылкой на документы..."}},
        "jur": {{"value": 4, "reason": "подробное обоснование юридического риска с ссылкой на документы..."}},
        "rep": {{"value": 4, "reason": "подробное обоснование репутационного риска с ссылкой на документы..."}},
        "strat": {{"value": 4, "reason": "подробное обоснование стратегического риска с ссылкой на документы..."}}
      }}
    }}
    """

    prompt = PromptTemplate.from_template(template)

    try:
        # Получаем русские названия для параметров
        access_ru = ACCESS_CATEGORIES.get(params.get('access_category', 'unknown'), 'Неизвестно')
        type_ru = RESOURCE_TYPES.get(params.get('resource_type', 'unknown'), 'Неизвестно')
        life_ru = LIFECYCLE.get(params.get('lifecycle', 'unknown'), 'Неизвестно')
        format_ru = FORMAT.get(params.get('data_format', 'unknown'), 'Неизвестно')
        scale_ru = SCALE.get(params.get('usage_scale', 'unknown'), 'Неизвестно')
        conf_ru = CONFIDENTIALITY.get(params.get('confidentiality', 'unknown'), 'Неизвестно')
        users_ru = USERS_COUNT.get(params.get('users_count', 'unknown'), 'Неизвестно')
        crit_ru = CRITICALITY.get(params.get('business_criticality', 'unknown'), 'Неизвестно')
        backup_ru = BACKUP.get(params.get('backup', 'unknown'), 'Неизвестно')

        formatted_prompt = prompt.format(
            resource_name=resource_name,
            resource_desc=resource_desc[:1000],
            access_category=access_ru,
            resource_type=type_ru,
            lifecycle=life_ru,
            data_format=format_ru,
            usage_scale=scale_ru,
            confidentiality=conf_ru,
            users_count=users_ru,
            business_criticality=crit_ru,
            backup=backup_ru,
            context=context
        )

        response = llm.invoke(formatted_prompt)
        result = extract_json(response)

        if result:
            return result
        else:
            return {"error": "Не удалось получить рекомендации", "raw": response[:500]}

    except Exception as e:
        return {"error": str(e)}