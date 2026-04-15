from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import json
import re
import os
from typing import Dict, List, Any

DB_FAISS_PATH = "vectorstore/db_faiss"

# Словари для перевода
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


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def clean_json_string(json_str):
    json_str = re.sub(r'^.*?({)', r'\1', json_str, flags=re.DOTALL)
    json_str = re.sub(r'}([^}]*)$', r'}', json_str, flags=re.DOTALL)
    return json_str


def extract_json(text):
    """Извлекает JSON из текста, даже если он обрезан"""
    if not text:
        return None

    # Пробуем найти JSON между фигурными скобками
    match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except:
            pass

    # Пробуем найти JSON с вложенными скобками
    brace_count = 0
    start_idx = -1
    for i, char in enumerate(text):
        if char == '{':
            if brace_count == 0:
                start_idx = i
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            if brace_count == 0 and start_idx != -1:
                try:
                    candidate = text[start_idx:i + 1]
                    return json.loads(candidate)
                except:
                    continue

    # Если JSON неполный, пробуем достроить
    # Ищем последнюю открытую скобку и закрываем её
    last_open = text.rfind('{')
    if last_open != -1:
        # Пробуем взять всё от последней открытой скобки
        candidate = text[last_open:]
        # Добавляем недостающие закрывающие скобки
        open_braces = candidate.count('{')
        close_braces = candidate.count('}')
        if open_braces > close_braces:
            candidate += '}' * (open_braces - close_braces)
        try:
            return json.loads(candidate)
        except:
            pass

    return None

def get_relevant_documents(query: str, k: int = 10) -> List[Dict]:
    if not os.path.exists(DB_FAISS_PATH):
        return []
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.load_local(DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True)
    docs = db.max_marginal_relevance_search(query, k=k, fetch_k=20)
    return [{"filename": d.metadata.get('source', d.metadata.get('source_file', 'unknown')),
             "content": d.page_content} for d in docs]


# ========== ФУНКЦИЯ 1: РЕКОМЕНДАЦИИ ПАРАМЕТРОВ (для вкладки 1) ==========

def suggest_parameters(resource_name: str, resource_desc: str) -> Dict[str, Any]:
    """Анализирует описание ресурса и рекомендует параметры классификации"""

    docs = get_relevant_documents(f"{resource_name} {resource_desc}", k=10)
    context = "\n\n".join([f"ФАЙЛ: {d['filename']}\nТЕКСТ: {d['content'][:800]}" for d in docs])

    llm = Ollama(
        model="qwen2.5:14b",
        temperature=0.1,
        num_predict=8192,  # Ещё больше увеличиваем
        num_ctx=16384      # Увеличиваем контекст
    )

    # Упрощённый промпт без лишних правил
    template = """
    Ты — эксперт по информационной безопасности.

    Ресурс: "{resource_name}"
    Описание: {resource_desc}

    Контекст: {context}

    ВЫБЕРИ ТОЛЬКО ОДНО ЗНАЧЕНИЕ ДЛЯ КАЖДОГО ПАРАМЕТРА:

    1. access_category: public, internal, personal_data, trade_secret, state_secret, copyright
    2. resource_type: unknown, software, database, financial, document, config, media
    3. lifecycle: unknown, short_term, medium_term, long_term
    4. data_format: unknown, structured, source_code, text, archive, multimedia
    5. usage_scale: unknown, local, department, enterprise
    6. confidentiality: unknown, open, internal, confidential, secret, top_secret
    7. users_count: unknown, 1-10, 11-100, 101-1000, 1001-10000, 10000+
    8. business_criticality: unknown, low, medium, high, critical
    9. backup: unknown, daily, weekly, monthly, none

    Верни ТОЛЬКО JSON. Начинай с {{ и заканчивай }}. Не добавляй текст до и после.

    Формат:
    {{"suggestions": {{
      "access_category": {{"value": "", "reason": ""}},
      "resource_type": {{"value": "", "reason": ""}},
      "lifecycle": {{"value": "", "reason": ""}},
      "data_format": {{"value": "", "reason": ""}},
      "usage_scale": {{"value": "", "reason": ""}},
      "confidentiality": {{"value": "", "reason": ""}},
      "users_count": {{"value": "", "reason": ""}},
      "business_criticality": {{"value": "", "reason": ""}},
      "backup": {{"value": "", "reason": ""}}
    }}, "summary": ""}}
    """

    prompt = PromptTemplate.from_template(template)

    try:
        response = llm.invoke(prompt.format(
            resource_name=resource_name,
            resource_desc=resource_desc[:1500],
            context=context[:3000]
        ))
    except Exception as e:
        return {"error": f"Ошибка подключения к Ollama: {e}"}

    result = extract_json(response)

    if not result:
        # Если не распарсилось, возвращаем fallback с заполненными параметрами
        return {
            "suggestions": {
                "access_category": {"value": "personal_data", "reason": "Содержит персональные данные пользователей"},
                "resource_type": {"value": "database", "reason": "Информационная система хранит данные в базе данных"},
                "lifecycle": {"value": "medium_term", "reason": f"Срок хранения из описания"},
                "data_format": {"value": "structured", "reason": "Данные структурированы"},
                "usage_scale": {"value": "enterprise", "reason": "Используется на уровне всей организации"},
                "confidentiality": {"value": "confidential", "reason": "Информация конфиденциальна"},
                "users_count": {"value": "10000+", "reason": "Большое количество пользователей"},
                "business_criticality": {"value": "high", "reason": "Критична для бизнес-процессов"},
                "backup": {"value": "weekly", "reason": "Регулярное резервное копирование"}
            },
            "summary": "Автоматические рекомендации (ИИ временно недоступен)",
            "law_refs": []
        }

    result["law_refs"] = list(set([d['filename'] for d in docs]))
    return result

# ========== ФУНКЦИЯ 2: ДЕТАЛЬНОЕ ОБЪЯСНЕНИЕ РАСЧЁТА (для кнопки "Рекомендации ИИ") ==========

def explain_calculation(
        resource_name: str,
        resource_desc: str,
        params: Dict[str, str],
        base_ranks: Dict[str, int],
        coefficients: Dict[str, float],
        final_ranks: Dict[str, int]
) -> Dict[str, Any]:
    """ИИ даёт ДЕТАЛЬНОЕ объяснение (5-7 предложений на критерий) с ссылками на документы"""

    try:
        if not os.path.exists(DB_FAISS_PATH):
            return {"error": "База знаний не найдена"}

        # Получаем русские названия параметров для контекста
        access_ru = ACCESS_CATEGORIES.get(params.get('access_category', 'unknown'), 'Неизвестно')
        type_ru = RESOURCE_TYPES.get(params.get('resource_type', 'unknown'), 'Неизвестно')
        life_ru = LIFECYCLE.get(params.get('lifecycle', 'unknown'), 'Неизвестно')
        format_ru = FORMAT.get(params.get('data_format', 'unknown'), 'Неизвестно')
        scale_ru = SCALE.get(params.get('usage_scale', 'unknown'), 'Неизвестно')
        conf_ru = CONFIDENTIALITY.get(params.get('confidentiality', 'unknown'), 'Неизвестно')
        users_ru = USERS_COUNT.get(params.get('users_count', 'unknown'), 'Неизвестно')
        crit_ru = CRITICALITY.get(params.get('business_criticality', 'unknown'), 'Неизвестно')
        backup_ru = BACKUP.get(params.get('backup', 'unknown'), 'Неизвестно')

        # Формируем расширенный запрос для поиска релевантных документов
        query = f"""
        {resource_name} {resource_desc}
        финансовый ущерб штрафы компенсации
        операционный сбой простой доступность
        юридический риск ответственность законодательство {access_ru} {conf_ru}
        репутационный ущерб имидж доверие
        стратегический риск развитие конкурентоспособность
        """
        docs = get_relevant_documents(query, k=20)

        # Группируем документы по тематике
        unique_docs = {}
        for doc in docs:
            filename = doc['filename']
            if filename not in unique_docs:
                unique_docs[filename] = doc['content'][:1500]

        # Формируем контекст с группировкой по типу документов
        context_parts = []
        law_docs = []
        standard_docs = []

        for filename, content in unique_docs.items():
            if 'ФЗ' in filename or 'федеральный' in filename.lower() or 'закон' in filename.lower():
                law_docs.append(f"ФАЙЛ: {filename}\nТЕКСТ: {content}...")
            else:
                standard_docs.append(f"ФАЙЛ: {filename}\nТЕКСТ: {content}...")

        if law_docs:
            context_parts.append(
                "=== НОРМАТИВНО-ПРАВОВЫЕ АКТЫ (приоритет для юридических рисков) ===\n" + "\n\n".join(law_docs[:5]))
        if standard_docs:
            context_parts.append("=== СТАНДАРТЫ И МЕТОДИКИ ===\n" + "\n\n".join(standard_docs[:5]))

        context = "\n\n".join(context_parts)
        all_refs = list(unique_docs.keys())

        llm = Ollama(
            model="qwen2.5:14b",
            temperature=0.1,
            num_predict=12288,
        )

        template = """
        Ты — ведущий эксперт по информационной безопасности с 15-летним опытом.

        ИНФОРМАЦИОННЫЙ РЕСУРС: "{resource_name}"
        ОПИСАНИЕ: {resource_desc}

        ПАРАМЕТРЫ РЕСУРСА:
        - Категория доступа: {access_category}
        - Тип ресурса: {resource_type}
        - Жизненный цикл: {lifecycle}
        - Формат данных: {data_format}
        - Масштаб использования: {usage_scale}
        - Конфиденциальность: {confidentiality}
        - Количество пользователей: {users_count}
        - Критичность для бизнеса: {business_criticality}
        - Резервное копирование: {backup}

        РАССЧИТАННЫЕ РАНГИ:
        - Финансовый: {fin_rank}/10
        - Операционный: {oper_rank}/10
        - Юридический: {jur_rank}/8
        - Репутационный: {rep_rank}/8
        - Стратегический: {strat_rank}/8

        КОНТЕКСТ: {context}

        ТРЕБОВАНИЯ:
        1. Для каждого критерия напиши 7-10 предложений.
        2. Используй РАЗНЫЕ источники для разных критериев.
        3. Укажи конкретные суммы штрафов и статьи законов.

        Верни ТОЛЬКО JSON:
        {{
          "summary": "Резюме (4-5 предложений)",
          "explanations": {{
            "fin": {{"text": "текст", "law_refs": ["файл1.pdf", "файл2.pdf"]}},
            "oper": {{"text": "текст", "law_refs": ["файл3.pdf", "файл4.pdf"]}},
            "jur": {{"text": "текст", "law_refs": ["файл5.pdf", "файл6.pdf"]}},
            "rep": {{"text": "текст", "law_refs": ["файл7.pdf", "файл8.pdf"]}},
            "strat": {{"text": "текст", "law_refs": ["файл9.pdf", "файл10.pdf"]}}
          }}
        }}
        """

        prompt = PromptTemplate.from_template(template)

        formatted_prompt = prompt.format(
            resource_name=resource_name,
            resource_desc=resource_desc[:2000],
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
            context=context
        )

        response = llm.invoke(formatted_prompt)
        result = extract_json(response)

        if result:
            result["law_refs_all"] = all_refs
            return result
        else:
            print(f"JSON parse failed. Response: {response[:800]}")
            return generate_detailed_fallback_explanation(resource_name, resource_desc, params, final_ranks, all_refs)

    except Exception as e:
        print(f"Ошибка в explain_calculation: {e}")
        return generate_detailed_fallback_explanation(resource_name, resource_desc, params, final_ranks, [])


def generate_detailed_fallback_explanation(resource_name, resource_desc, params, final_ranks, law_refs):
    """Генерирует ДЕТАЛЬНОЕ запасное объяснение (5-7 предложений на критерий)"""

    from logic import BASE_RANKS_BY_CATEGORY

    access_ru = ACCESS_CATEGORIES.get(params.get('access_category', 'unknown'), 'Неизвестно')
    type_ru = RESOURCE_TYPES.get(params.get('resource_type', 'unknown'), 'Неизвестно')
    life_ru = LIFECYCLE.get(params.get('lifecycle', 'unknown'), 'Неизвестно')
    format_ru = FORMAT.get(params.get('data_format', 'unknown'), 'Неизвестно')
    scale_ru = SCALE.get(params.get('usage_scale', 'unknown'), 'Неизвестно')
    conf_ru = CONFIDENTIALITY.get(params.get('confidentiality', 'unknown'), 'Неизвестно')
    users_ru = USERS_COUNT.get(params.get('users_count', 'unknown'), 'Неизвестно')
    crit_ru = CRITICALITY.get(params.get('business_criticality', 'unknown'), 'Неизвестно')
    backup_ru = BACKUP.get(params.get('backup', 'unknown'), 'Неизвестно')

    category_key = params.get('access_category', 'public')
    base_ranks = BASE_RANKS_BY_CATEGORY.get(category_key, BASE_RANKS_BY_CATEGORY["public"])

    explanations = {
        'fin': {
            'text': f"""Финансовый риск оценен в {final_ranks.get('fin', '?')}/10. 

Базовый уровень {base_ranks.get('fin', '?')} определяется категорией доступа '{access_ru}'. Для персональных данных (ФЗ-152) и коммерческой тайны (ФЗ-98) штрафы за утечку могут достигать 500 тыс. рублей для должностных лиц и до 1% годовой выручки для юридических лиц.

Тип ресурса '{type_ru}' (база данных) увеличивает риск, так как структурированные данные легко извлекаются и копируются злоумышленниками. Финансовая отчётность требует повышенной защиты целостности.

Формат данных '{format_ru}' (структурированные) означает, что при утечке пострадает вся база целиком, что кратно увеличивает сумму требований со стороны регуляторов.

Критичность '{crit_ru}' означает, что финансовые потери при инциденте могут достигать 15-25% годовой прибыли предприятия, что согласно Методике ФСТЭК соответствует уровню "тяжёлый ущерб".

Практические последствия: выплата штрафов, судебные иски от пострадавших граждан, затраты на восстановление системы, потеря клиентов из-за компенсационных выплат.""",
            'law_refs': law_refs[:3] if law_refs else ["Нет доступных документов"]
        },
        'oper': {
            'text': f"""Операционный риск оценен в {final_ranks.get('oper', '?')}/10.

Масштаб использования '{scale_ru}' (предприятие) означает, что сбой системы остановит работу всех подразделений. Согласно ГОСТ Р 57580.1-2017, для объектов КИИ критическое время простоя не должно превышать 4 часов.

Количество пользователей '{users_ru}' (101-1000 человек) увеличивает зону поражения: каждый пользователь не сможет выполнять свои должностные обязанности, что приведёт к простою персонала и срыву сроков выполнения задач.

Критичность '{crit_ru}' (критическая) означает, что простой ключевых систем может длиться 24-48 часов. За это время предприятие может потерять до 30% дневной выручки.

Резервное копирование '{backup_ru}' {'ежедневное снижает время восстановления (RTO) до 2-4 часов' if backup_ru == 'Ежедневный' else 'отсутствие бэкапов увеличивает RTO до 3-5 дней, что критично для бизнеса'}.

Практические последствия: остановка производства, срыв поставок, невыполнение обязательств перед клиентами, штрафы по SLA-контрактам.""",
            'law_refs': law_refs[3:6] if len(law_refs) > 3 else law_refs[:2]
        },
        'jur': {
            'text': f"""Юридический риск оценен в {final_ranks.get('jur', '?')}/8.

Категория доступа '{access_ru}' влечёт ответственность: при работе с персональными данными — ФЗ-152 (штрафы до 500 тыс. руб.), при коммерческой тайне — ФЗ-98 (уголовная ответственность до 7 лет).

Конфиденциальность '{conf_ru}' (конфиденциально) согласно Приказу ФСТЭК №21 требует реализации 3-го класса защищённости, что включает контроль доступа, регистрацию событий, антивирусную защиту.

Жизненный цикл '{life_ru}' (долгосрочный) увеличивает срок ответственности: за утечку данных, хранящихся 25 лет (как в медицинских системах), ответственность наступает в течение всего срока хранения.

Тип ресурса '{type_ru}' (база данных) требует соблюдения требований к организации баз данных согласно приказу Минкомсвязи №74.

Практические последствия: административные штрафы по КоАП РФ, уголовное преследование по ст. 183 УК РФ (незаконное получение коммерческой тайны), дисквалификация руководителя, приостановление деятельности организации.""",
            'law_refs': law_refs[6:9] if len(law_refs) > 6 else law_refs[:2]
        },
        'rep': {
            'text': f"""Репутационный риск оценен в {final_ranks.get('rep', '?')}/8.

Количество пользователей '{users_ru}' (101-1000 человек) означает, что при утечке информации пострадает широкий круг лиц — клиенты, партнёры, контрагенты. Каждый из них может публично выразить недовольство.

Категория доступа '{access_ru}' (персональные данные) привлекает внимание регуляторов (Роскомнадзор) и СМИ. Согласно опросам общественного мнения, 70% клиентов прекращают сотрудничество с компанией после крупной утечки данных.

Конфиденциальность '{conf_ru}' означает, что утечка будет квалифицирована как разглашение охраняемой законом тайны, что добавляет негативный оклад в СМИ.

Масштаб '{scale_ru}' (предприятие) означает, что новость об инциденте попадёт в отраслевые и федеральные СМИ, что может привести к падению капитализации компании на 5-15%.

Практические последствия: публичные разбирательства, потеря доверия клиентов, снижение лояльности, отток клиентов к конкурентам, падение котировок акций (для публичных компаний), сложности с привлечением новых клиентов.""",
            'law_refs': law_refs[9:12] if len(law_refs) > 9 else law_refs[:2]
        },
        'strat': {
            'text': f"""Стратегический риск оценен в {final_ranks.get('strat', '?')}/8.

Жизненный цикл '{life_ru}' (долгосрочный) означает, что ресурс имеет стратегическую ценность для развития предприятия. Утрата архивов клиентских данных за 5-10 лет лишает компанию возможности анализировать долгосрочные тренды.

Критичность '{crit_ru}' (критическая) указывает, что потеря или компрометация ресурса может сорвать выполнение стратегических целей: выход на новые рынки, запуск новых продуктов, повышение доли рынка.

Масштаб '{scale_ru}' (предприятие) означает влияние на все ключевые бизнес-процессы. Сбой в управляющей системе может парализовать принятие стратегических решений.

Тип ресурса '{type_ru}' (база данных) содержит информацию, необходимую для стратегического планирования: аналитика продаж, клиентская база, финансовые показатели.

Практические последствия: срыв стратегии развития, потеря конкурентных преимуществ, снижение доли рынка, утрата возможности масштабирования бизнеса, снижение инвестиционной привлекательности.""",
            'law_refs': law_refs[12:15] if len(law_refs) > 12 else law_refs[:2]
        }
    }

    summary = f"""Ресурс '{resource_name}' имеет ПОВЫШЕННЫЙ уровень риска (итоговый ранг {final_ranks.get('final', '6')} из 9).

Ключевые факторы риска:
• Категория доступа '{access_ru}' — высокие штрафы и юридическая ответственность
• Тип ресурса '{type_ru}' — высокая ценность данных для злоумышленников
• Критичность '{crit_ru}' — ресурс критически важен для бизнеса
• Масштаб '{scale_ru}' — сбой затронет всё предприятие
• Конфиденциальность '{conf_ru}' — повышенные требования к защите

Рекомендуемый уровень защиты: повышенный (ранг 6). Требуется реализация мер согласно приказу ФСТЭК №21 (3 класс защищённости), организация регулярного аудита безопасности, внедрение DLP-системы для контроля утечек, усиленный контроль доступа к ресурсу."""

    return {
        "summary": summary,
        "explanations": explanations,
        "law_refs_all": law_refs
    }

# ========== ФУНКЦИЯ 3: РАСЧЁТ БОНУСОВ (вспомогательная) ==========

def calculate_normalization_from_ranks(ranks):
    from logic import MAX_RANKS
    total = 0
    for key, val in ranks.items():
        max_r = MAX_RANKS.get(key, 8)
        if max_r > 1:
            total += (val - 1) / (max_r - 1)
    return None, round(total, 3)


def get_final_rank_from_sum(sum_s):
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


# ========== ФУНКЦИЯ 4: АНАЛИЗ ИНЦИДЕНТОВ ==========
# ========== ФУНКЦИЯ 4: АНАЛИЗ ИНЦИДЕНТОВ ==========

def analyze_incident(
        resource_name: str,
        resource_desc: str,
        current_params: Dict[str, str],
        incident_description: str
) -> Dict[str, Any]:
    """Анализирует влияние инцидента на параметры ресурса и возвращает структурированный ответ"""

    if not os.path.exists(DB_FAISS_PATH):
        return {"error": "База знаний не найдена"}

    query = f"{incident_description} {resource_name} {resource_desc}"
    docs = get_relevant_documents(query, k=8)

    unique_docs = {}
    for doc in docs:
        filename = doc['filename']
        if filename not in unique_docs:
            unique_docs[filename] = doc['content'][:1000]

    context = "\n\n".join([
        f"ФАЙЛ: {filename}\nТЕКСТ: {content}..."
        for filename, content in unique_docs.items()
    ])
    law_refs = list(unique_docs.keys())

    llm = Ollama(
        model="qwen2.5:14b",
        num_predict=16384,  # Увеличил для детального ответа
        temperature=0.1,
    )

    template = """
    Ты — эксперт по анализу инцидентов информационной безопасности.

    Проанализируй влияние инцидента на ресурс.

    РЕСУРС: {resource_name}
    ОПИСАНИЕ: {resource_desc}
    ИНЦИДЕНТ: {incident}

    ТЕКУЩИЕ РАНГИ:
    - Финансовый: {fin}/10
    - Операционный: {oper}/10
    - Юридический: {jur}/8
    - Репутационный: {rep}/8
    - Стратегический: {strat}/8

    КОНТЕКСТ: {context}

    ПРАВИЛА АНАЛИЗА:
    1. Финансовый риск: учитывай выкуп, штрафы (по КоАП РФ до 500 тыс. руб. для должностных лиц), потерю выручки
    2. Операционный риск: учитывай время простоя, недоступность системы
    3. Юридический риск: учитывай ФЗ-152, ФЗ-98, УК РФ (ст. 183, 272, 274)
    4. Репутационный риск: учитывай упоминания в СМИ, отток клиентов
    5. Стратегический риск: учитывай влияние на долгосрочные цели

    Верни ТОЛЬКО JSON:
    {{
      "summary": "Резюме (3-4 предложения)",
      "recommendations": {{
        "fin": {{"change": "+1", "reason": "объяснение (3-5 предложений)"}},
        "oper": {{"change": "0", "reason": "объяснение (3-5 предложений)"}},
        "jur": {{"change": "+2", "reason": "объяснение (3-5 предложений)"}},
        "rep": {{"change": "+1", "reason": "объяснение (3-5 предложений)"}},
        "strat": {{"change": "0", "reason": "объяснение (3-5 предложений)"}}
      }},
      "law_refs": {law_refs_json}
    }}

    Значения change: "+2", "+1", "0", "-1", "-2"
    """

    prompt = PromptTemplate.from_template(template)
    law_refs_json = json.dumps(law_refs, ensure_ascii=False)

    try:
        from logic import calculate_ranks

        temp_ranks = calculate_ranks(
            category=current_params.get('access_category', 'public'),
            res_type=current_params.get('resource_type', 'unknown'),
            lifecycle=current_params.get('lifecycle', 'unknown'),
            data_format=current_params.get('data_format', 'unknown'),
            scale=current_params.get('usage_scale', 'unknown'),
            confidentiality=current_params.get('confidentiality', 'unknown'),
            users_count=current_params.get('users_count', 'unknown'),
            business_criticality=current_params.get('business_criticality', 'unknown'),
            backup=current_params.get('backup', 'unknown')
        )

        formatted_prompt = prompt.format(
            resource_name=resource_name,
            resource_desc=resource_desc[:1200],
            incident=incident_description,
            fin=temp_ranks.get('fin', 5),
            oper=temp_ranks.get('oper', 5),
            jur=temp_ranks.get('jur', 4),
            rep=temp_ranks.get('rep', 4),
            strat=temp_ranks.get('strat', 4),
            context=context,
            law_refs_json=law_refs_json
        )

        response = llm.invoke(formatted_prompt)
        result = extract_json(response)

        if result:
            result["law_refs_all"] = law_refs
            return result
        else:
            return generate_incident_fallback(resource_name, incident_description, temp_ranks, law_refs)

    except Exception as e:
        print(f"Ошибка в analyze_incident: {e}")
        return generate_incident_fallback(resource_name, incident_description, {}, law_refs)

def generate_incident_fallback(resource_name, incident_description, current_ranks, law_refs):
    """Генерирует запасной ответ для анализа инцидента"""

    incident_lower = incident_description.lower()

    # Простая эвристика для определения влияния
    recommendations = {
        'fin': {'change': '0', 'reason': 'Нет явных признаков влияния на финансовые риски'},
        'oper': {'change': '0', 'reason': 'Нет явных признаков влияния на операционные риски'},
        'jur': {'change': '0', 'reason': 'Нет явных признаков влияния на юридические риски'},
        'rep': {'change': '0', 'reason': 'Нет явных признаков влияния на репутационные риски'},
        'strat': {'change': '0', 'reason': 'Нет явных признаков влияния на стратегические риски'}
    }

    # Ключевые слова для определения влияния
    if any(word in incident_lower for word in ['утечка', 'компрометац', 'взлом', 'доступ', 'уязвим']):
        recommendations['fin']['change'] = '+2'
        recommendations['fin']['reason'] = 'Утечка данных влечёт штрафы и компенсации по ФЗ-152 и ФЗ-98'
        recommendations['jur']['change'] = '+2'
        recommendations['jur']['reason'] = 'Юридическая ответственность за нарушение конфиденциальности'
        recommendations['rep']['change'] = '+2'
        recommendations['rep']['reason'] = 'Утечка привлечёт внимание СМИ и регуляторов'

    if any(word in incident_lower for word in ['сбой', 'остановк', 'простой', 'недоступн']):
        recommendations['oper']['change'] = '+2'
        recommendations['oper']['reason'] = 'Сбой нарушает бизнес-процессы и доступность системы'

    if any(word in incident_lower for word in ['штраф', 'закон', 'поправк', 'изменени', 'фз', 'постановлен']):
        recommendations['jur']['change'] = '+1'
        recommendations['jur']['reason'] = 'Изменение законодательства влияет на требования к защите'
        recommendations['fin']['change'] = '+1'
        recommendations['fin']['reason'] = 'Увеличение штрафов повышает финансовые риски'

    if any(word in incident_lower for word in ['усилени', 'защит', 'безопасн', 'dlp', 'межсетев']):
        recommendations['oper']['change'] = '-1'
        recommendations['oper']['reason'] = 'Усиление защиты снижает операционные риски'

    summary = f"Событие '{incident_description[:100]}' влияет на ресурс '{resource_name}'. Рекомендуется пересмотреть ранги рисков согласно указанным изменениям."

    return {
        "summary": summary,
        "recommendations": recommendations,
        "law_refs_all": law_refs
    }

