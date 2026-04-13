import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import modules.ai_analyst as ai
import database as db
import logic

# Настройка страницы (ТОЛЬКО ОДИН РАЗ!)
st.set_page_config(
    page_title="СППР Оценка динамики ценности ИР",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* СВЕТЛЫЙ ФОН И ЧЁРНЫЙ ТЕКСТ */
    .stApp {
        background-color: #f5f5f5 !important;
    }

    .stApp, .stMarkdown, .stText, .stInfo, .stSuccess, .stWarning, .stError,
    p, li, span, div, label, .stTextInput label, .stTextArea label {
        color: #000000 !important;
        font-size: 18px !important;
    }

    /* ЗАГОЛОВКИ */
    h1, h2, h3, h4 {
        color: #000000 !important;
    }
    h1 {
        font-size: 2.5rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
    }
    h2 {
        font-size: 1.8rem !important;
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
    }

    /* ТАБЫ */
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #000000 !important;
        background-color: #e0e0e0 !important;
        border-radius: 8px 8px 0 0 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem !important;
    }

    /* КНОПКИ */
    .stButton button {
        font-size: 1rem !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        border-radius: 8px !important;
        background-color: #4CAF50 !important;
        color: white !important;
        border: none !important;
    }
    .stButton button:hover {
        background-color: #45a049 !important;
    }

    /* МЕТРИКИ */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: #000000 !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
        color: #333333 !important;
    }
    [data-testid="stMetricDelta"] {
        color: #333333 !important;
    }

    /* ПОЛЯ ВВОДА */
    .stTextInput input, .stTextArea textarea, .stSelectbox select {
        font-size: 1rem !important;
        padding: 0.5rem !important;
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
        border-radius: 6px !important;
    }

    /* ЛЕЙБЛЫ */
    .stTextInput label, .stTextArea label, .stSelectbox label, .stSlider label {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #000000 !important;
    }

    /* СЛАЙДЕРЫ */
    .stSlider {
        padding: 0.5rem 0 !important;
    }

    /* ТАБЛИЦЫ */
    .stTable td, .stTable th, .dataframe td, .dataframe th {
        font-size: 14px !important;
        padding: 8px 10px !important;
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #dddddd !important;
    }

    /* EXPANDER */
    .streamlit-expanderHeader {
        font-size: 1rem !important;
        font-weight: 600 !important;
        background-color: #e8e8e8 !important;
        color: #000000 !important;
        border-radius: 8px !important;
    }
    .streamlit-expanderContent {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 8px !important;
    }

    /* ИНФО БЛОКИ */
    .stInfo {
        background-color: #d9edf7 !important;
        color: #000000 !important;
        border-left: 4px solid #31708f !important;
    }
    .stSuccess {
        background-color: #dff0d8 !important;
        color: #000000 !important;
        border-left: 4px solid #3c763d !important;
    }
    .stWarning {
        background-color: #fcf8e3 !important;
        color: #000000 !important;
        border-left: 4px solid #8a6d3b !important;
    }
    .stError {
        background-color: #f2dede !important;
        color: #000000 !important;
        border-left: 4px solid #a94442 !important;
    }

    /* КАРТОЧКИ РЕЗУЛЬТАТОВ */
    .result-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 1rem;
        text-align: center;
    }
    .result-card h4 {
        font-size: 0.9rem !important;
        color: white !important;
    }
    .result-card p {
        font-size: 1.8rem !important;
        font-weight: bold;
        color: white !important;
    }

    /* КАРТОЧКИ РИСКОВ */
    .risk-card {
        background: #f0f2f6 !important;
        padding: 0.8rem;
        border-radius: 10px;
        border-left: 4px solid;
        color: #000000 !important;
    }
    .risk-card strong {
        font-size: 0.9rem !important;
        color: #000000 !important;
    }
    .risk-card span {
        font-size: 1.5rem !important;
        font-weight: bold;
        color: #000000 !important;
    }

    /* ПОДВАЛ */
    footer {
        font-size: 0.8rem !important;
        color: #666666 !important;
    }

    /* БЛОКИ */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0 !important;
    }

    /* ВСПЛЫВАЮЩИЕ УВЕДОМЛЕНИЯ */
    .stToast {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    .stSelectbox div[data-baseweb="select"] > div,
    .stSelectbox ul,
    .stSelectbox div[role="listbox"],
    div[data-baseweb="select"] div {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Выпадающий список */
    .stSelectbox div[data-baseweb="select"] ul {
        background-color: #ffffff !important;
    }
    
    /* Элементы выпадающего списка */
    .stSelectbox li {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    .stSelectbox li:hover {
        background-color: #e0e0e0 !important;
    }
    
    /* Текст в выбранном элементе */
    .stSelectbox div[data-baseweb="select"] div {
        color: #000000 !important;
    }
    
    /* Радиокнопки и чекбоксы */
    .stRadio div, .stCheckbox div {
        background-color: transparent !important;
    }
    
    /* Слайдеры */
    .stSlider div {
        background-color: transparent !important;
    }
    
    /* Date input */
    .stDateInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Number input */
    .stNumberInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Tabs фон */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent !important;
    }
    
    /* Выбранный таб */
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    
    /* Невыбранный таб */
    .stTabs [data-baseweb="tab"] {
        background-color: #e0e0e0 !important;
        color: #000000 !important;
    }
    
    /* Selectbox стрелка */
    .stSelectbox svg {
        fill: #000000 !important;
    }
    
    /* Инпуты */
    .stTextInput input, .stTextArea textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
    }
    
    /* Селектор ресурса (специально) */
    div[data-testid="stSelectbox"] label {
        color: #000000 !important;
    }
    
    /* Контейнер выбора ресурса */
    .stSelectbox [data-baseweb="select"] {
        background-color: #ffffff !important;
    }
    /* Основной контейнер выпадающего списка */
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
        border-radius: 8px !important;
    }
    
    /* Список внутри выпадающего окна */
    div[data-baseweb="popover"] ul {
        background-color: #ffffff !important;
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Элементы списка */
    div[data-baseweb="popover"] li {
        background-color: #ffffff !important;
        color: #000000 !important;
        padding: 8px 12px !important;
        cursor: pointer !important;
    }
    
    /* Элементы списка при наведении */
    div[data-baseweb="popover"] li:hover {
        background-color: #e0e0e0 !important;
    }
    
    /* Выбранный элемент в списке */
    div[data-baseweb="popover"] li[aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    
    /* Контейнер выбранного значения */
    div[data-baseweb="select"] div[aria-selected="true"] {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    
    /* Затемнение фона (backdrop) */
    div[data-radix-portal] {
        background-color: rgba(0,0,0,0.1) !important;
    }
    
    /* Все popup окна Streamlit */
    .stPopover, .stTooltip, .stTooltipContent {
        background-color: #ffffff !important;
        border: 1px solid #cccccc !important;
    }
    
    /* Date picker */
    div[data-baseweb="calendar"] {
        background-color: #ffffff !important;
    }
    div[data-baseweb="calendar"] div {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Функция для создания красивых карточек рисков
def display_risk_card(title, value, max_val, color_class):
    st.markdown(f"""
    <div class="risk-card {color_class}">
        <strong>{title}</strong><br>
        <span style="font-size: 1.8rem; font-weight: bold;">{value}</span>
        <span style="font-size: 1rem;">/{max_val}</span>
    </div>
    """, unsafe_allow_html=True)


# Функция для создания красивой метрики
def display_metric(label, value, unit=""):
    st.markdown(f"""
    <div class="result-card">
        <h4>{label}</h4>
        <p>{value}{unit}</p>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ СЕССИИ
# ============================================================================
def init_session_state():
    """Инициализация всех переменных состояния сессии"""
    if "ai_suggestions" not in st.session_state:
        st.session_state.ai_suggestions = None
    if "ai_law_refs" not in st.session_state:
        st.session_state.ai_law_refs = []
    if "ai_summary" not in st.session_state:
        st.session_state.ai_summary = ""
    if "resource_saved" not in st.session_state:
        st.session_state.resource_saved = False
    if "current_resource_id" not in st.session_state:
        st.session_state.current_resource_id = None
    if "selected_resource_for_analysis" not in st.session_state:
        st.session_state.selected_resource_for_analysis = None
    if "calculation_explanation" not in st.session_state:
        st.session_state.calculation_explanation = None
    if "current_calculation" not in st.session_state:
        st.session_state.current_calculation = None
    if "calculation_result" not in st.session_state:
        st.session_state.calculation_result = None
    if "incident_analysis" not in st.session_state:
        st.session_state.incident_analysis = None
        if "ai_explanation" not in st.session_state:
            st.session_state.ai_explanation = None


init_session_state()


# ============================================================================
# ФУНКЦИЯ ВАЛИДАЦИИ РЕКОМЕНДАЦИЙ ИИ
# ============================================================================
def validate_ai_suggestions(suggestions, resource_desc):
    """
    УНИВЕРСАЛЬНАЯ проверка и корректировка ошибок ИИ
    Работает для любых чисел: 1, 10, 100, 500, 758, 1000, 1500, 10000, 500000
    """

    desc_lower = resource_desc.lower()
    import re

    # =========================================================================
    # 1. ОПРЕДЕЛЕНИЕ КАТЕГОРИИ ДОСТУПА
    # =========================================================================

    # Признаки коммерческой тайны
    commercial_keywords = [
        'номенклатур', 'цена', 'цен', 'закупк', 'поставщик', 'производств',
        'себестоим', 'финанс', 'управленческ', 'коммерческ', 'бизнес',
        'рынок', 'конкурент', 'сделк', 'договор', 'контракт', 'клиент',
        'партнер', 'поставк', 'склад', 'логистик', 'калькуляц'
    ]

    # Признаки персональных данных
    personal_keywords = [
        'фио', 'фамили', 'имя', 'отчеств', 'паспорт', 'снилс', 'инн',
        'телефон', 'email', 'почт', 'адрес', 'дата рождени', 'возраст',
        'место рождени', 'гражданств', 'национальност', 'фотографи',
        'биометрическ', 'медицинск', 'диагноз', 'состояние здоров'
    ]

    # Признаки гостайны
    state_keywords = ['гостайн', 'государственна тайн', 'секретно', 'совершенно секретно', 'особой важности']

    # Определяем категорию доступа
    has_commercial = any(word in desc_lower for word in commercial_keywords)
    has_personal = any(word in desc_lower for word in personal_keywords)
    has_state = any(word in desc_lower for word in state_keywords)

    if has_state:
        suggestions["access_category"] = {
            "value": "state_secret",
            "reason": "Информация составляет государственную тайну"
        }
    elif has_commercial and not has_personal:
        suggestions["access_category"] = {
            "value": "trade_secret",
            "reason": "Ресурс содержит коммерческую тайну предприятия"
        }
    elif has_personal:
        suggestions["access_category"] = {
            "value": "personal_data",
            "reason": "Ресурс содержит персональные данные физических лиц"
        }

    # =========================================================================
    # 2. ОПРЕДЕЛЕНИЕ ТИПА РЕСУРСА
    # =========================================================================

    # Признаки базы данных
    database_keywords = [
        'база данн', 'бд', 'хранилищ', 'таблиц', 'sql', 'postgresql',
        'oracle', 'mysql', 'mongodb', 'электронн таблиц', 'реестр',
        'каталог', 'справочник', 'журнал', 'регистр'
    ]

    # Признаки ПО
    software_keywords = [
        'программ', 'приложени', 'систем', 'модул', 'скрипт', 'алгоритм',
        'сервис', 'платформа', 'интерфейс', 'api', 'веб', 'мобильн'
    ]

    # Признаки финансовой отчетности
    financial_keywords = [
        'отчетност', 'баланс', 'бухгалтер', 'финанс', 'налог', 'декларац'
    ]

    if any(word in desc_lower for word in database_keywords):
        suggestions["resource_type"] = {
            "value": "database",
            "reason": "Ресурс представляет собой базу данных"
        }
    elif any(word in desc_lower for word in software_keywords):
        suggestions["resource_type"] = {
            "value": "software",
            "reason": "Ресурс является программным обеспечением"
        }
    elif any(word in desc_lower for word in financial_keywords):
        suggestions["resource_type"] = {
            "value": "financial",
            "reason": "Ресурс содержит финансовую отчетность"
        }

    # =========================================================================
    # 3. ОПРЕДЕЛЕНИЕ КОЛИЧЕСТВА ПОЛЬЗОВАТЕЛЕЙ (УНИВЕРСАЛЬНОЕ)
    # =========================================================================

    # Функция для извлечения ВСЕХ чисел из текста с контекстом
    def extract_numbers_with_context(text, keywords):
        """
        Извлекает числа, которые находятся рядом с ключевыми словами
        Работает с числами: 1, 10, 100, 500, 758, 1000, 1500, 10000, 500000
        """
        results = []

        # Паттерн для чисел с возможными пробелами (например "1 500")
        number_pattern = r'(\d{1,3}(?:[\s]?\d{3})*)'

        for keyword in keywords:
            # Ищем числа перед ключевым словом
            pattern_before = r'(\d{1,3}(?:[\s]?\d{3})*)\s*' + keyword
            matches_before = re.findall(pattern_before, text)
            for match in matches_before:
                clean_num = match.replace(' ', '')
                try:
                    results.append(int(clean_num))
                except:
                    pass

            # Ищем числа после ключевого слова
            pattern_after = keyword + r'\s*(\d{1,3}(?:[\s]?\d{3})*)'
            matches_after = re.findall(pattern_after, text)
            for match in matches_after:
                clean_num = match.replace(' ', '')
                try:
                    results.append(int(clean_num))
                except:
                    pass

            # Ищем числа с плюсом: "500+ сотрудников"
            pattern_plus = r'(\d{1,3}(?:[\s]?\d{3})*)\+\s*' + keyword
            matches_plus = re.findall(pattern_plus, text)
            for match in matches_plus:
                clean_num = match.replace(' ', '')
                try:
                    results.append(int(clean_num))
                except:
                    pass

        return results

    # Ключевые слова для поиска
    user_keywords = [
        'сотрудник', 'работник', 'персонал', 'человек', 'пользовател',
        'клиент', 'покупател', 'врач', 'медсестр', 'медицинск', 'учител',
        'студент', 'учащийся', 'сотр', 'чел'
    ]

    # Извлекаем все числа
    all_numbers = extract_numbers_with_context(desc_lower, user_keywords)

    # Если не нашли, пробуем другой подход — ищем любые числа и проверяем контекст
    if not all_numbers:
        # Ищем любые числа от 1 до 999999
        any_numbers = re.findall(r'(\d{1,6})', desc_lower)
        for num_str in any_numbers:
            try:
                num = int(num_str)
                # Проверяем, есть ли рядом ключевое слово
                position = desc_lower.find(num_str)
                context = desc_lower[max(0, position - 40):min(len(desc_lower), position + 40)]
                if any(keyword in context for keyword in user_keywords):
                    all_numbers.append(num)
            except:
                pass

    # Определяем максимальное число
    if all_numbers:
        max_users = max(all_numbers)

        # Определяем тип системы (клиентская или внутренняя)
        client_keywords = ['клиент', 'покупател', 'банк', 'магазин', 'сервис', 'платформа']
        is_client_system = any(word in desc_lower for word in client_keywords)

        # Определяем диапазон
        if max_users >= 10000:
            suggestions["users_count"] = {
                "value": "10000+",
                "reason": f"В описании указано {max_users} пользователей/сотрудников"
            }
        elif max_users >= 1000:
            suggestions["users_count"] = {
                "value": "1001-10000",
                "reason": f"В описании указано {max_users} пользователей/сотрудников"
            }
        elif max_users >= 100:
            suggestions["users_count"] = {
                "value": "101-1000",
                "reason": f"В описании указано {max_users} пользователей/сотрудников"
            }
        elif max_users >= 11:
            suggestions["users_count"] = {
                "value": "11-100",
                "reason": f"В описании указано {max_users} пользователей/сотрудников"
            }
        elif max_users >= 1:
            suggestions["users_count"] = {
                "value": "1-10",
                "reason": f"В описании указано {max_users} пользователей/сотрудников"
            }
    else:
        # Если не нашли чисел, оставляем то, что предложил ИИ
        pass

    # =========================================================================
    # 4. ОПРЕДЕЛЕНИЕ ФОРМАТА ДАННЫХ
    # =========================================================================

    # Признаки структурированных данных
    structured_keywords = [
        'база данн', 'бд', 'таблиц', 'sql', 'postgresql', 'oracle', 'mysql',
        'реестр', 'каталог', 'справочник', 'журнал', 'регистр', 'json', 'xml',
        'структурирован', 'электронн таблиц', 'excel', 'google sheets'
    ]

    # Признаки исходного кода
    source_keywords = [
        'исходный код', 'программ', 'скрипт', 'алгоритм', 'разработк',
        'репозиторий', 'git', 'svn', 'библиотек', 'функци'
    ]

    # Признаки текстовых документов
    text_keywords = [
        'документ', 'текст', 'файл', 'отчёт', 'письмо', 'инструкци',
        'регламент', 'положени', 'приказ', 'распоряжени', 'акт', 'договор'
    ]

    if any(word in desc_lower for word in structured_keywords):
        suggestions["data_format"] = {
            "value": "structured",
            "reason": "Данные структурированы и организованы"
        }
    elif any(word in desc_lower for word in source_keywords):
        suggestions["data_format"] = {
            "value": "source_code",
            "reason": "Ресурс содержит исходный код или скрипты"
        }
    elif any(word in desc_lower for word in text_keywords):
        suggestions["data_format"] = {
            "value": "text",
            "reason": "Данные представлены в виде текстовых документов"
        }

    # =========================================================================
    # 5. ОПРЕДЕЛЕНИЕ ЖИЗНЕННОГО ЦИКЛА
    # =========================================================================

    # Ищем срок хранения в годах
    year_pattern = r'(\d+)\s*лет'
    years_match = re.findall(year_pattern, desc_lower)

    if years_match:
        max_years = max(int(y) for y in years_match)
        if max_years >= 3:
            suggestions["lifecycle"] = {
                "value": "long_term",
                "reason": f"Срок хранения данных составляет {max_years} лет"
            }
        elif max_years >= 1:
            suggestions["lifecycle"] = {
                "value": "medium_term",
                "reason": f"Срок хранения данных составляет {max_years} года"
            }
    else:
        # Если не нашли года, ищем ключевые слова
        if any(word in desc_lower for word in ['долгосроч', 'длительн', 'многолет', 'архив']):
            suggestions["lifecycle"] = {
                "value": "long_term",
                "reason": "Ресурс имеет долгосрочный характер хранения"
            }
        elif any(word in desc_lower for word in ['краткосроч', 'быстро устарев']):
            suggestions["lifecycle"] = {
                "value": "short_term",
                "reason": "Ресурс имеет краткосрочный характер"
            }

    # =========================================================================
    # 6. ОПРЕДЕЛЕНИЕ КРИТИЧНОСТИ
    # =========================================================================

    critical_keywords = [
        'критич', 'остановк', 'невозможн', 'теряет', 'без ресурс',
        'простой', 'аварий', 'катастроф', 'жизненно важн', 'ключевой',
        'основной бизнес', 'производств останавл', 'сервис недоступ'
    ]

    if any(word in desc_lower for word in critical_keywords):
        suggestions["business_criticality"] = {
            "value": "critical",
            "reason": "Ресурс критически важен для бизнес-процессов"
        }
    elif any(word in desc_lower for word in ['важн', 'значим', 'основн']):
        suggestions["business_criticality"] = {
            "value": "high",
            "reason": "Ресурс имеет высокую важность для бизнеса"
        }

    # =========================================================================
    # 7. ОПРЕДЕЛЕНИЕ БЭКАПА
    # =========================================================================

    if any(word in desc_lower for word in ['ежедневн', 'каждый день', 'daily']):
        suggestions["backup"] = {
            "value": "daily",
            "reason": "Резервное копирование выполняется ежедневно"
        }
    elif any(word in desc_lower for word in ['еженедельн', 'раз в неделю', 'weekly']):
        suggestions["backup"] = {
            "value": "weekly",
            "reason": "Резервное копирование выполняется еженедельно"
        }
    elif any(word in desc_lower for word in ['ежемесячн', 'раз в месяц', 'monthly']):
        suggestions["backup"] = {
            "value": "monthly",
            "reason": "Резервное копирование выполняется ежемесячно"
        }
    elif any(word in desc_lower for word in ['нет бэкап', 'отсутству', 'не производит']):
        suggestions["backup"] = {
            "value": "none",
            "reason": "Резервное копирование отсутствует"
        }

    # =========================================================================
    # 8. ОПРЕДЕЛЕНИЕ МАСШТАБА
    # =========================================================================

    if any(word in desc_lower for word in ['все подразделени', 'всей организации', 'все предприяти', 'корпоративн']):
        suggestions["usage_scale"] = {
            "value": "enterprise",
            "reason": "Ресурс используется во всех подразделениях предприятия"
        }
    elif any(word in desc_lower for word in ['отдел', 'департамент', 'подразделени']):
        suggestions["usage_scale"] = {
            "value": "department",
            "reason": "Ресурс используется на уровне отдела"
        }
    elif any(word in desc_lower for word in ['рабочее место', 'локальн', 'отдельн сотрудник']):
        suggestions["usage_scale"] = {
            "value": "local",
            "reason": "Ресурс используется локально"
        }
    # =========================================================================
    # 9. КОРРЕКТИРОВКА ТИПА РЕСУРСА
    # =========================================================================
    if suggestions.get("resource_type", {}).get("value") == "software":
        db_indicators = ['данные о', 'содержит данные', 'хранит', 'клиентах', 'заказах', 'база данн', 'бд']
        if any(word in desc_lower for word in db_indicators):
            suggestions["resource_type"] = {
                "value": "database",
                "reason": "Ресурс является базой данных, содержащей структурированную информацию"
            }

    # =========================================================================
    # 10. КОРРЕКТИРОВКА ФОРМАТА ДАННЫХ
    # =========================================================================
    if suggestions.get("data_format", {}).get("value") == "text":
        structured_indicators = ['клиентах', 'заказах', 'данные о', 'база', 'таблиц', 'структурирован']
        if any(word in desc_lower for word in structured_indicators):
            suggestions["data_format"] = {
                "value": "structured",
                "reason": "Данные структурированы и организованы в базе данных"
            }

    # =========================================================================
    # 11. КОРРЕКТИРОВКА КОНФИДЕНЦИАЛЬНОСТИ
    # =========================================================================
    if suggestions.get("confidentiality", {}).get("value") in ["secret", "top_secret"]:
        state_keywords = ['гостайн', 'государственна тайн', 'особой важности']
        if not any(word in desc_lower for word in state_keywords):
            suggestions["confidentiality"] = {
                "value": "confidential",
                "reason": "Информация является конфиденциальной, но не составляет государственную тайну"
            }

    return suggestions

    return suggestions
# ============================================================================
# СЛОВАРИ ДЛЯ ПЕРЕВОДА
# ============================================================================
RUSSIAN_ACCESS = {
    "public": "📢 Общедоступная",
    "internal": "🏢 Внутренняя (ДСП)",
    "personal_data": "👤 Персональные данные (ПДн)",
    "trade_secret": "🔒 Коммерческая тайна (КТ)",
    "state_secret": "⚡ Государственная тайна",
    "copyright": "© Интеллектуальная собственность"
}

RUSSIAN_TYPE = {
    "unknown": "❓ Неизвестно",
    "software": "💻 Программное обеспечение",
    "database": "🗄️ База данных",
    "financial": "💰 Финансовая отчетность",
    "document": "📄 Текстовая документация",
    "config": "⚙️ Конфигурационные файлы",
    "media": "🎬 Мультимедиа"
}

RUSSIAN_LIFE = {
    "unknown": "❓ Неизвестно",
    "short_term": "⏱️ Краткосрочный (дни/месяцы)",
    "medium_term": "📅 Среднесрочный (до 1 года)",
    "long_term": "📆 Долгосрочный (более 1 года)"
}

RUSSIAN_FORMAT = {
    "unknown": "❓ Неизвестно",
    "structured": "🗂️ Структурированные (БД/JSON)",
    "source_code": "👨‍💻 Исходный код",
    "text": "📝 Текстовые документы",
    "archive": "📦 Архивы",
    "multimedia": "🎥 Мультимедиа"
}

RUSSIAN_SCALE = {
    "unknown": "❓ Неизвестно",
    "local": "👤 Локальный",
    "department": "👥 Уровень отдела",
    "enterprise": "🏭 Масштаб предприятия"
}

RUSSIAN_CONFIDENTIALITY = {
    "unknown": "❓ Неизвестно",
    "open": "🔓 Открытая информация",
    "internal": "🏢 Для внутреннего пользования",
    "confidential": "🔒 Конфиденциально",
    "secret": "⚡ Секретно",
    "top_secret": "🛡️ Особой важности"
}

RUSSIAN_USERS = {
    "unknown": "❓ Неизвестно",
    "1-10": "👤 1-10 пользователей",
    "11-100": "👥 11-100 пользователей",
    "101-1000": "👥👥 101-1000 пользователей",
    "1001-10000": "🏢 1001-10000 пользователей",
    "10000+": "🌐 Более 10000 пользователей"
}

RUSSIAN_CRITICALITY = {
    "unknown": "❓ Неизвестно",
    "low": "🟢 Низкая",
    "medium": "🟡 Средняя",
    "high": "🟠 Высокая",
    "critical": "🔴 Критическая"
}

RUSSIAN_BACKUP = {
    "unknown": "❓ Неизвестно",
    "daily": "✅ Ежедневный",
    "weekly": "📅 Еженедельный",
    "monthly": "📆 Ежемесячный",
    "none": "❌ Отсутствует"
}

# Обратные словари
REVERSE_ACCESS = {v: k for k, v in RUSSIAN_ACCESS.items()}
REVERSE_TYPE = {v: k for k, v in RUSSIAN_TYPE.items()}
REVERSE_LIFE = {v: k for k, v in RUSSIAN_LIFE.items()}
REVERSE_FORMAT = {v: k for k, v in RUSSIAN_FORMAT.items()}
REVERSE_SCALE = {v: k for k, v in RUSSIAN_SCALE.items()}
REVERSE_CONFIDENTIALITY = {v: k for k, v in RUSSIAN_CONFIDENTIALITY.items()}
REVERSE_USERS = {v: k for k, v in RUSSIAN_USERS.items()}
REVERSE_CRITICALITY = {v: k for k, v in RUSSIAN_CRITICALITY.items()}
REVERSE_BACKUP = {v: k for k, v in RUSSIAN_BACKUP.items()}


# ============================================================================
# ЗАГОЛОВОК
# ============================================================================
st.title("🛡️ Система поддержки принятия решений для оценки динамики ценности информационных ресурсов")
st.markdown("---")

with st.expander("📚 О методике оценки (бонусная система)", expanded=False):
    st.markdown("""
    ### Математическая модель оценки ценности ИР (бонусная система)

    **Принцип расчёта:** каждый параметр ресурса даёт прибавку (+1) к определённым критериям риска.

    **Группа А (шкала 1-10):**
    - **Финансовый ущерб (fin)** - прямые и косвенные потери
    - **Операционный сбой (oper)** - влияние на бизнес-процессы

    **Группа Б (шкала 1-8):**
    - **Юридический риск (jur)** - ответственность по НПА
    - **Репутационный ущерб (rep)** - имиджевые потери
    - **Стратегический ущерб (strat)** - влияние на развитие

    **Как формируется ранг:**
    1. Базовые ранги от категории доступа
    2. + бонусы от типа ресурса
    3. + бонусы от жизненного цикла
    4. + бонусы от формата данных
    5. + бонусы от масштаба
    6. + бонусы от конфиденциальности
    7. + бонусы от количества пользователей
    8. + бонусы от критичности
    9. ± бонус/штраф от резервного копирования

    **Нормализация:** $S_{критерий} = \\frac{R_{факт} - 1}{R_{max} - 1}$

    **Итоговый ранг ценности** (1-9) определяется по интегральной сумме $S_\\Sigma$
    """)


# ============================================================================
# ОСНОВНЫЕ ВКЛАДКИ
# ============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 1. Регистрация и базовая оценка",
    "📊 2. Анализ ранга сохраненного ресурса",
    "⚡ 3. Динамика и инциденты",
    "📚 4. База ресурсов и отчеты"
])


# ============================================================================
# ВКЛАДКА 1: РЕГИСТРАЦИЯ НОВОГО РЕСУРСА
# ============================================================================
# Вкладка 1
with tab1:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**📋 Исходные данные**")

        resource_name = st.text_input(
            "Название ресурса *",
            placeholder="Например: Медицинская информационная система",
            key="input_name"
        )

        resource_desc = st.text_area(
            "Описание ресурса",
            placeholder="Опишите назначение, содержание, кто работает с ресурсом, срок хранения, формат данных, количество пользователей...",
            height=150,
            key="input_desc"
        )

        col_ai_btn, col_ai_status = st.columns([1, 2])
        with col_ai_btn:
            ai_request_btn = st.button(
                "🤖 Запросить рекомендации ИИ",
                type="secondary",
                width="stretch",
                disabled=not (resource_name and resource_desc)
            )
        with col_ai_status:
            if st.session_state.ai_suggestions:
                st.success("✅ Рекомендации получены")
            else:
                st.info("⏳ ИИ проанализирует описание")

        # Обработка запроса к ИИ
        if ai_request_btn and resource_name and resource_desc:
            with st.spinner("🔍 ИИ анализирует..."):
                analysis = ai.suggest_parameters(resource_name, resource_desc)

                if "error" not in analysis:
                    suggestions = analysis.get("suggestions", {})
                    suggestions = validate_ai_suggestions(suggestions, resource_desc)

                    st.session_state.ai_suggestions = suggestions
                    st.session_state.ai_law_refs = analysis.get("law_refs", [])
                    st.session_state.ai_summary = analysis.get("summary", "")
                    st.session_state.resource_saved = False
                    st.rerun()
                else:
                    st.error(f"Ошибка: {analysis['error']}")

        if st.session_state.ai_suggestions:
            with st.expander("🤖 Рекомендации ИИ-ассистента", expanded=True):
                if st.session_state.ai_summary:
                    st.markdown(f"**📝 Резюме:** {st.session_state.ai_summary}")

                suggestions = st.session_state.ai_suggestions

                col_rec1, col_rec2 = st.columns(2)
                with col_rec1:
                    if "access_category" in suggestions:
                        acc = suggestions["access_category"]
                        st.info(
                            f"**Доступ:** {RUSSIAN_ACCESS.get(acc.get('value', 'public'), acc.get('value', 'public'))}\n\n*{acc.get('reason', '')}*")
                    if "resource_type" in suggestions:
                        rt = suggestions["resource_type"]
                        st.info(
                            f"**Тип:** {RUSSIAN_TYPE.get(rt.get('value', 'unknown'), rt.get('value', 'unknown'))}\n\n*{rt.get('reason', '')}*")
                    if "lifecycle" in suggestions:
                        lc = suggestions["lifecycle"]
                        st.info(
                            f"**Жизненный цикл:** {RUSSIAN_LIFE.get(lc.get('value', 'unknown'), lc.get('value', 'unknown'))}\n\n*{lc.get('reason', '')}*")
                with col_rec2:
                    if "usage_scale" in suggestions:
                        us = suggestions["usage_scale"]
                        st.info(
                            f"**Масштаб:** {RUSSIAN_SCALE.get(us.get('value', 'unknown'), us.get('value', 'unknown'))}\n\n*{us.get('reason', '')}*")
                    if "confidentiality" in suggestions:
                        conf = suggestions["confidentiality"]
                        st.info(
                            f"**Конфиденциальность:** {RUSSIAN_CONFIDENTIALITY.get(conf.get('value', 'unknown'), conf.get('value', 'unknown'))}\n\n*{conf.get('reason', '')}*")
                    if "users_count" in suggestions:
                        users = suggestions["users_count"]
                        st.info(
                            f"**Пользователей:** {RUSSIAN_USERS.get(users.get('value', 'unknown'), users.get('value', 'unknown'))}\n\n*{users.get('reason', '')}*")

    with col2:
        st.markdown("**⚙️ Параметры классификации**")

        suggested_access = suggested_type = suggested_life = suggested_format = None
        suggested_scale = suggested_conf = suggested_users = suggested_crit = suggested_backup = None

        if st.session_state.ai_suggestions:
            suggested_access = st.session_state.ai_suggestions.get("access_category", {}).get("value")
            suggested_type = st.session_state.ai_suggestions.get("resource_type", {}).get("value")
            suggested_life = st.session_state.ai_suggestions.get("lifecycle", {}).get("value")
            suggested_format = st.session_state.ai_suggestions.get("data_format", {}).get("value")
            suggested_scale = st.session_state.ai_suggestions.get("usage_scale", {}).get("value")
            suggested_conf = st.session_state.ai_suggestions.get("confidentiality", {}).get("value")
            suggested_users = st.session_state.ai_suggestions.get("users_count", {}).get("value")
            suggested_crit = st.session_state.ai_suggestions.get("business_criticality", {}).get("value")
            suggested_backup = st.session_state.ai_suggestions.get("backup", {}).get("value")

        st.markdown("**Основные параметры:**")
        col_a1, col_a2 = st.columns(2)

        with col_a1:
            sel_access = st.selectbox(
                "Категория доступа *",
                options=list(RUSSIAN_ACCESS.keys()),
                format_func=lambda x: RUSSIAN_ACCESS[x],
                index=0 if not suggested_access else list(RUSSIAN_ACCESS.keys()).index(
                    suggested_access) if suggested_access in RUSSIAN_ACCESS else 0,
                key="expert_access"
            )
            sel_type = st.selectbox(
                "Тип ресурса *",
                options=list(RUSSIAN_TYPE.keys()),
                format_func=lambda x: RUSSIAN_TYPE[x],
                index=0 if not suggested_type else list(RUSSIAN_TYPE.keys()).index(
                    suggested_type) if suggested_type in RUSSIAN_TYPE else 0,
                key="expert_type"
            )
            sel_life = st.selectbox(
                "Жизненный цикл *",
                options=list(RUSSIAN_LIFE.keys()),
                format_func=lambda x: RUSSIAN_LIFE[x],
                index=0 if not suggested_life else list(RUSSIAN_LIFE.keys()).index(
                    suggested_life) if suggested_life in RUSSIAN_LIFE else 0,
                key="expert_life"
            )

        with col_a2:
            sel_format = st.selectbox(
                "Формат данных *",
                options=list(RUSSIAN_FORMAT.keys()),
                format_func=lambda x: RUSSIAN_FORMAT[x],
                index=0 if not suggested_format else list(RUSSIAN_FORMAT.keys()).index(
                    suggested_format) if suggested_format in RUSSIAN_FORMAT else 0,
                key="expert_format"
            )
            sel_scale = st.selectbox(
                "Масштаб использования *",
                options=list(RUSSIAN_SCALE.keys()),
                format_func=lambda x: RUSSIAN_SCALE[x],
                index=0 if not suggested_scale else list(RUSSIAN_SCALE.keys()).index(
                    suggested_scale) if suggested_scale in RUSSIAN_SCALE else 0,
                key="expert_scale"
            )

        st.markdown("**🔍 Дополнительные параметры:**")
        col_new1, col_new2 = st.columns(2)

        with col_new1:
            sel_conf = st.selectbox(
                "Уровень конфиденциальности",
                options=list(RUSSIAN_CONFIDENTIALITY.keys()),
                format_func=lambda x: RUSSIAN_CONFIDENTIALITY[x],
                index=0 if not suggested_conf else list(RUSSIAN_CONFIDENTIALITY.keys()).index(
                    suggested_conf) if suggested_conf in RUSSIAN_CONFIDENTIALITY else 0,
                key="expert_conf"
            )
            sel_users = st.selectbox(
                "Количество пользователей",
                options=list(RUSSIAN_USERS.keys()),
                format_func=lambda x: RUSSIAN_USERS[x],
                index=0 if not suggested_users else list(RUSSIAN_USERS.keys()).index(
                    suggested_users) if suggested_users in RUSSIAN_USERS else 0,
                key="expert_users"
            )

        with col_new2:
            sel_crit = st.selectbox(
                "Критичность для бизнеса",
                options=list(RUSSIAN_CRITICALITY.keys()),
                format_func=lambda x: RUSSIAN_CRITICALITY[x],
                index=0 if not suggested_crit else list(RUSSIAN_CRITICALITY.keys()).index(
                    suggested_crit) if suggested_crit in RUSSIAN_CRITICALITY else 0,
                key="expert_crit"
            )
            sel_backup = st.selectbox(
                "Резервное копирование",
                options=list(RUSSIAN_BACKUP.keys()),
                format_func=lambda x: RUSSIAN_BACKUP[x],
                index=0 if not suggested_backup else list(RUSSIAN_BACKUP.keys()).index(
                    suggested_backup) if suggested_backup in RUSSIAN_BACKUP else 0,
                key="expert_backup"
            )

        st.markdown("---")
        if st.button("💾 Сохранить ресурс", type="primary", width="stretch", disabled=not resource_name):
            res_id = db.add_resource(
                name=resource_name,
                description=resource_desc,
                category=RUSSIAN_ACCESS[sel_access],
                res_type=RUSSIAN_TYPE[sel_type],
                lifecycle=RUSSIAN_LIFE[sel_life],
                data_format=RUSSIAN_FORMAT[sel_format],
                scale=RUSSIAN_SCALE[sel_scale],
                confidentiality=RUSSIAN_CONFIDENTIALITY[sel_conf],
                users_count=RUSSIAN_USERS[sel_users],
                business_criticality=RUSSIAN_CRITICALITY[sel_crit],
                backup=RUSSIAN_BACKUP[sel_backup]
            )
            st.session_state.current_resource_id = res_id
            st.session_state.resource_saved = True
            st.session_state.selected_resource_for_analysis = res_id

            st.toast(f"✅ Ресурс сохранён! ID: {res_id}", icon="✅")
            st.success(f"✅ Ресурс '{resource_name}' успешно сохранен! ID: {res_id}")
            st.balloons()
            import time

            time.sleep(1.5)
            st.rerun()

# ============================================================================
# ВКЛАДКА 2: АНАЛИЗ РАНГА СОХРАНЕННОГО РЕСУРСА (с ползунками и ИИ)
# ============================================================================
with tab2:
    st.markdown("<h2 style='font-size: 2.2rem;'>📊 Анализ ранга сохраненного ресурса</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.8rem;'>📋 Параметры ресурса</h3>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.8rem;'>⚙️ Экспертная оценка</h3>", unsafe_allow_html=True)
    st.header("📊 Анализ ранга сохраненного ресурса")

    resources = db.get_all_resources_full()

    if not resources:
        st.info("ℹ️ База данных пуста. Сначала добавьте ресурс на первой вкладке.")
    else:
        col_select, col_btn = st.columns([3, 1])

        with col_select:
            resource_options = {r[0]: f"{r[0]}: {r[1]} ({r[2]})" for r in resources}
            default_idx = 0
            if st.session_state.selected_resource_for_analysis:
                ids = list(resource_options.keys())
                if st.session_state.selected_resource_for_analysis in ids:
                    default_idx = ids.index(st.session_state.selected_resource_for_analysis)
            selected_res_id = st.selectbox(
                "Выберите ресурс для анализа",
                options=list(resource_options.keys()),
                format_func=lambda x: resource_options[x],
                index=default_idx,
                key="analysis_res_selector"
            )

        with col_btn:
            load_btn = st.button("📥 Загрузить ресурс", type="primary", use_container_width=True)

        if load_btn and selected_res_id:
            st.session_state.selected_resource_for_analysis = selected_res_id
            st.session_state.calculation_explanation = None
            st.session_state.current_calculation = None
            st.session_state.calculation_result = None
            st.rerun()

        if st.session_state.selected_resource_for_analysis:
            resource_data = db.get_resource_full_by_id(st.session_state.selected_resource_for_analysis)

            if resource_data:
                if len(resource_data) >= 13:
                    (res_id, res_name, res_desc, res_category, res_type, res_life,
                     res_format, res_scale, res_conf, res_users, res_crit, res_backup, created_at) = resource_data
                else:
                    res_id, res_name, res_desc, res_category, res_type, res_life, res_format, res_scale, created_at = resource_data
                    res_conf = res_users = res_crit = res_backup = "❓ Неизвестно"

                st.markdown("---")
                st.subheader(f"📋 Параметры ресурса: {res_name}")

                col_params1, col_params2, col_params3 = st.columns(3)
                with col_params1:
                    st.info(f"**Категория доступа:** {res_category}")
                    st.info(f"**Тип ресурса:** {res_type}")
                    st.info(f"**Жизненный цикл:** {res_life}")
                with col_params2:
                    st.info(f"**Формат данных:** {res_format}")
                    st.info(f"**Масштаб:** {res_scale}")
                    st.info(f"**Конфиденциальность:** {res_conf}")
                with col_params3:
                    st.info(f"**Пользователей:** {res_users}")
                    st.info(f"**Критичность:** {res_crit}")
                    st.info(f"**Бэкап:** {res_backup}")

                with st.expander("📝 Полное описание"):
                    st.write(res_desc)

                # Преобразуем русские названия в ключи
                category_key = REVERSE_ACCESS.get(res_category, "public")
                type_key = REVERSE_TYPE.get(res_type, "unknown")
                life_key = REVERSE_LIFE.get(res_life, "unknown")
                format_key = REVERSE_FORMAT.get(res_format, "unknown")
                scale_key = REVERSE_SCALE.get(res_scale, "unknown")
                conf_key = REVERSE_CONFIDENTIALITY.get(res_conf, "unknown")
                users_key = REVERSE_USERS.get(res_users, "unknown")
                crit_key = REVERSE_CRITICALITY.get(res_crit, "unknown")
                backup_key = REVERSE_BACKUP.get(res_backup, "unknown")

                # Получаем рекомендованные ранги от системы (на основе параметров)
                recommended_ranks = logic.calculate_ranks(
                    category=category_key,
                    res_type=type_key,
                    lifecycle=life_key,
                    data_format=format_key,
                    scale=scale_key,
                    confidentiality=conf_key,
                    users_count=users_key,
                    business_criticality=crit_key,
                    backup=backup_key
                )

                # Получаем детали бонусов
                bonus_details = logic.get_bonus_details(
                    category=category_key,
                    res_type=type_key,
                    lifecycle=life_key,
                    data_format=format_key,
                    scale=scale_key,
                    confidentiality=conf_key,
                    users_count=users_key,
                    business_criticality=crit_key,
                    backup=backup_key
                )

                # История оценок
                history = db.get_evaluation_history(res_id)

                # ========== БЛОК ЭКСПЕРТНОЙ ОЦЕНКИ С ПОЛЗУНКАМИ ==========
                st.markdown("---")
                st.subheader("⚙️ Экспертная оценка (выставьте ранги вручную)")

                # Значения по умолчанию = рекомендованные системой
                default_fin = recommended_ranks['fin']
                default_oper = recommended_ranks['oper']
                default_jur = recommended_ranks['jur']
                default_rep = recommended_ranks['rep']
                default_strat = recommended_ranks['strat']

                # Если есть история, берем последние значения (переопределяем)
                if history:
                    last_eval = history[-1]
                    default_fin = last_eval[3]
                    default_oper = last_eval[4]
                    default_jur = last_eval[5]
                    default_rep = last_eval[6]
                    default_strat = last_eval[7]

                # Ползунки для эксперта
                col_sl1, col_sl2 = st.columns(2)

                with col_sl1:
                    expert_fin = st.slider(
                        "💰 Финансовый риск (1-10)",
                        1, 10, default_fin,
                        help="Оцените потенциальные финансовые потери",
                        key=f"expert_fin_{res_id}"
                    )
                    expert_oper = st.slider(
                        "⚙️ Операционный риск (1-10)",
                        1, 10, default_oper,
                        help="Оцените влияние на бизнес-процессы",
                        key=f"expert_oper_{res_id}"
                    )
                    expert_jur = st.slider(
                        "⚖️ Юридический риск (1-8)",
                        1, 8, default_jur,
                        help="Оцените юридические последствия",
                        key=f"expert_jur_{res_id}"
                    )

                with col_sl2:
                    expert_rep = st.slider(
                        "📢 Репутационный риск (1-8)",
                        1, 8, default_rep,
                        help="Оцените влияние на репутацию",
                        key=f"expert_rep_{res_id}"
                    )
                    expert_strat = st.slider(
                        "🚩 Стратегический риск (1-8)",
                        1, 8, default_strat,
                        help="Оцените влияние на стратегию",
                        key=f"expert_strat_{res_id}"
                    )

                # ========== ОТОБРАЖЕНИЕ БОНУСНОЙ СИСТЕМЫ (ВСЕГДА) ==========
                with st.expander("📊 Как формируются рекомендованные ранги (бонусная система)", expanded=False):
                    st.markdown("### Шаг 1: Базовые ранги от категории доступа")
                    base_data = {
                        "Критерий": ["💰 Финансовый", "⚙️ Операционный", "⚖️ Юридический", "📢 Репутационный",
                                     "🚩 Стратегический"],
                        "Базовый ранг": [
                            bonus_details['base']['fin'],
                            bonus_details['base']['oper'],
                            bonus_details['base']['jur'],
                            bonus_details['base']['rep'],
                            bonus_details['base']['strat']
                        ]
                    }
                    st.table(pd.DataFrame(base_data))

                    if bonus_details['bonuses']:
                        st.markdown("### Шаг 2: Добавление бонусов от параметров")
                        for bonus in bonus_details['bonuses']:
                            st.markdown(f"**+ {bonus['source']}:** {bonus['bonus']}")

                    st.markdown("### Итоговые рекомендованные ранги")
                    final_data = {
                        "Критерий": ["💰 Финансовый", "⚙️ Операционный", "⚖️ Юридический", "📢 Репутационный",
                                     "🚩 Стратегический"],
                        "Рекомендованный ранг": [
                            recommended_ranks['fin'],
                            recommended_ranks['oper'],
                            recommended_ranks['jur'],
                            recommended_ranks['rep'],
                            recommended_ranks['strat']
                        ],
                        "Максимум": ["10", "10", "8", "8", "8"]
                    }
                    st.table(pd.DataFrame(final_data))
                    st.caption("💡 Эти значения установлены в ползунках по умолчанию. Вы можете их скорректировать.")

                # ========== КНОПКИ ==========
                st.markdown("---")
                col_ai, col_calc, col_save = st.columns([1, 1, 1])

                with col_ai:
                    ai_recommend_btn = st.button(
                        "🤖 Рекомендации ИИ",
                        type="secondary",
                        use_container_width=True,
                        help="ИИ проанализирует ресурс и даст детальное обоснование рангов"
                    )

                with col_calc:
                    calculate_expert_btn = st.button(
                        "🧮 Рассчитать итоговый ранг",
                        type="primary",
                        use_container_width=True,
                        help="Рассчитать интегральный S∑ и итоговый ранг по текущим значениям ползунков"
                    )

                with col_save:
                    save_direct_btn = st.button(
                        "💾 Сохранить текущую оценку",
                        type="secondary",
                        use_container_width=True,
                        help="Сохранить оценку без расчёта"
                    )

                # ========== ОБРАБОТКА: РЕКОМЕНДАЦИИ ИИ (только обоснование) ==========
                if ai_recommend_btn:
                    with st.spinner("🤖 ИИ анализирует ресурс и формирует детальное экспертное заключение..."):
                        params_for_ai = {
                            'access_category': category_key,
                            'resource_type': type_key,
                            'lifecycle': life_key,
                            'data_format': format_key,
                            'usage_scale': scale_key,
                            'confidentiality': conf_key,
                            'users_count': users_key,
                            'business_criticality': crit_key,
                            'backup': backup_key
                        }

                        base_ranks = logic.BASE_RANKS_BY_CATEGORY.get(category_key, {})
                        coefficients = {
                            'type': 1.0, 'lifecycle': 1.0, 'format': 1.0, 'scale': 1.0,
                            'conf': 1.0, 'users': 1.0, 'business': 1.0, 'backup': 1.0
                        }

                        # Берём текущие значения с ползунков (или рекомендованные)
                        current_expert_ranks = {
                            'fin': expert_fin,
                            'oper': expert_oper,
                            'jur': expert_jur,
                            'rep': expert_rep,
                            'strat': expert_strat
                        }

                        explanation = ai.explain_calculation(
                            res_name, res_desc, params_for_ai, base_ranks, coefficients, current_expert_ranks
                        )

                        if "error" not in explanation:
                            st.session_state.ai_explanation = explanation
                            st.success("✅ Экспертное заключение ИИ получено! Разверните блок ниже.")
                        else:
                            st.warning(
                                f"ИИ не смог сформировать заключение: {explanation.get('error', 'Неизвестная ошибка')}")

                # ========== ПОКАЗ ЭКСПЕРТНОГО ЗАКЛЮЧЕНИЯ ИИ (если есть) ==========
                if st.session_state.get("ai_explanation"):
                    with st.expander("📚 Экспертное заключение ИИ (на основе НПА)", expanded=True):
                        exp = st.session_state.ai_explanation

                        if "summary" in exp:
                            st.info(f"**Общее заключение:** {exp['summary']}")

                        if "explanations" in exp:
                            crit_names = {
                                'fin': '💰 Финансовый риск',
                                'oper': '⚙️ Операционный риск',
                                'jur': '⚖️ Юридический риск',
                                'rep': '📢 Репутационный риск',
                                'strat': '🚩 Стратегический риск'
                            }

                            for crit, title in crit_names.items():
                                if crit in exp["explanations"]:
                                    st.markdown(f"### {title}")
                                    st.markdown(exp["explanations"][crit].get("text", "Нет объяснения"))

                                    law_refs = exp["explanations"][crit].get("law_refs", [])
                                    if law_refs:
                                        unique_refs = list(set(law_refs))
                                        st.caption("📄 **Источники:** " + ", ".join(unique_refs))
                                    st.markdown("---")

                # ========== ОБРАБОТКА: ПРЯМОЕ СОХРАНЕНИЕ ==========
                # ========== ОБРАБОТКА: ПРЯМОЕ СОХРАНЕНИЕ ==========
                if save_direct_btn:
                    expert_ranks = {
                        'fin': expert_fin,
                        'oper': expert_oper,
                        'jur': expert_jur,
                        'rep': expert_rep,
                        'strat': expert_strat
                    }

                    s_scores, total_s = logic.calculate_normalization(expert_ranks)
                    final_rank = logic.get_final_rank(total_s)

                    details = {
                        'expert_ranks': expert_ranks,
                        'total_s': total_s,
                        'final_rank': final_rank,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }

                    db.save_evaluation(
                        resource_id=res_id,
                        ranks=expert_ranks,
                        norm_score=total_s,
                        final_rank=final_rank,
                        trigger="Экспертная оценка (прямое сохранение)",
                        details=details
                    )

                    # Уведомления
                    st.toast(f"✅ Оценка сохранена! Итоговый ранг: {final_rank}", icon="✅")
                    st.success(f"✅ Оценка сохранена! Итоговый ранг: {final_rank}")
                    st.balloons()

                    import time

                    time.sleep(1.5)
                    st.rerun()
                # ========== ОБРАБОТКА: РАСЧЁТ ИТОГОВОГО РАНГА (только цифры) ==========
                if calculate_expert_btn:
                    expert_ranks = {
                        'fin': expert_fin,
                        'oper': expert_oper,
                        'jur': expert_jur,
                        'rep': expert_rep,
                        'strat': expert_strat
                    }

                    s_scores, total_s = logic.calculate_normalization(expert_ranks)
                    final_rank = logic.get_final_rank(total_s)
                    protection_level = logic.get_protection_level(final_rank)

                    st.session_state.calculation_result = {
                        'expert_ranks': expert_ranks,
                        's_scores': s_scores,
                        'total_s': total_s,
                        'final_rank': final_rank,
                        'protection_level': protection_level
                    }

                # ========== ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ РАСЧЁТА (только цифры) ==========
                if st.session_state.get("calculation_result"):
                    result = st.session_state.calculation_result

                    st.markdown("---")
                    st.subheader("📊 Результаты расчета")

                    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                    with col_m1:
                        st.metric("💰 Финансовый", f"{result['expert_ranks']['fin']}/10")
                    with col_m2:
                        st.metric("⚙️ Операционный", f"{result['expert_ranks']['oper']}/10")
                    with col_m3:
                        st.metric("⚖️ Юридический", f"{result['expert_ranks']['jur']}/8")
                    with col_m4:
                        st.metric("📢 Репутационный", f"{result['expert_ranks']['rep']}/8")
                    with col_m5:
                        st.metric("🚩 Стратегический", f"{result['expert_ranks']['strat']}/8")


                    col_i1, col_i2, col_i3 = st.columns(3)
                    with col_i1:
                        display_metric("📈 Интегральный S∑", f"{total_s:.3f}")
                    with col_i2:
                        display_metric("🏆 Итоговый ранг", str(final_rank))
                    with col_i3:
                        display_metric("🛡️ Уровень защиты", protection_level)

                    # Детали нормализации
                    with st.expander("📐 Детали нормализации (S)", expanded=False):
                        norm_data = {
                            "Критерий": ["Финансовый", "Операционный", "Юридический", "Репутационный",
                                         "Стратегический"],
                            "S (нормализованный)": [
                                f"{result['s_scores']['fin']:.3f}",
                                f"{result['s_scores']['oper']:.3f}",
                                f"{result['s_scores']['jur']:.3f}",
                                f"{result['s_scores']['rep']:.3f}",
                                f"{result['s_scores']['strat']:.3f}"
                            ],
                            "Формула": [
                                f"({result['expert_ranks']['fin']} - 1) / 9",
                                f"({result['expert_ranks']['oper']} - 1) / 9",
                                f"({result['expert_ranks']['jur']} - 1) / 7",
                                f"({result['expert_ranks']['rep']} - 1) / 7",
                                f"({result['expert_ranks']['strat']} - 1) / 7"
                            ]
                        }
                        st.table(pd.DataFrame(norm_data))

                    # Кнопка сохранения после расчёта
                    st.markdown("---")
                    col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
                    with col_save2:
                        if st.button("💾 Сохранить оценку в историю", width="stretch"):
                            details = {
                                'expert_ranks': result['expert_ranks'],
                                's_scores': result['s_scores'],
                                'total_s': result['total_s'],
                                'final_rank': result['final_rank']
                            }

                            db.save_evaluation(
                                resource_id=res_id,
                                ranks=result['expert_ranks'],
                                norm_score=result['total_s'],
                                final_rank=result['final_rank'],
                                trigger="Экспертная оценка (после расчёта)",
                                details=details
                            )

                            st.toast(f"✅ Оценка сохранена! Итоговый ранг: {result['final_rank']}", icon="✅")
                            st.success(f"✅ Оценка сохранена! Итоговый ранг: {result['final_rank']}")
                            st.balloons()

                            import time

                            time.sleep(1.5)
                            st.rerun()

# ============================================================================
# ВКЛАДКА 3: ДИНАМИКА И ИНЦИДЕНТЫ
# ============================================================================
with tab3:
    st.markdown("<h2 style='font-size: 2.2rem;'>⚡ Анализ динамики ценности при инцидентах</h2>", unsafe_allow_html=True)
    st.markdown("<h3 style='font-size: 1.8rem;'>📈 Динамика изменения ценности</h3>", unsafe_allow_html=True)
    st.header("⚡ Анализ динамики ценности при инцидентах")

    resources = db.get_all_resources_full()

    if not resources:
        st.info("ℹ️ База данных пуста. Сначала добавьте ресурс на первой вкладке.")
    else:
        res_dict = {r[0]: f"ID {r[0]}: {r[1]} ({r[2]})" for r in resources}
        selected_res_id = st.selectbox(
            "Выберите ресурс для анализа динамики",
            options=list(res_dict.keys()),
            format_func=lambda x: res_dict[x],
            key="incident_res_selector"
        )

        history = db.get_evaluation_history(selected_res_id)

        if not history:
            st.warning("⚠️ Для этого ресурса еще нет оценок. Сначала проведите анализ на вкладке 2.")
        else:
            st.subheader("📈 Динамика изменения ценности")

            df_history = pd.DataFrame(
                history,
                columns=["Дата", "Событие", "Ранг", "Фин", "Опер", "Юр", "Реп", "Страт", "S∑", "Детали"]
            )

            if len(df_history) > 1:
                chart_data = df_history[["Дата", "Ранг"]].copy()
                chart_data["Дата"] = pd.to_datetime(chart_data["Дата"])
                chart_data = chart_data.set_index("Дата")
                st.line_chart(chart_data)
            else:
                st.info("ℹ️ Для построения графика нужно минимум 2 оценки")

            with st.expander("📋 История оценок", expanded=False):
                display_df = df_history.drop(columns=["Детали"] if "Детали" in df_history.columns else [])
                st.dataframe(display_df, use_container_width=True)

            st.markdown("---")

            resource_data = db.get_resource_full_by_id(selected_res_id)
            if resource_data:
                if len(resource_data) >= 13:
                    (res_id, res_name, res_desc, res_category, res_type, res_life,
                     res_format, res_scale, res_conf, res_users, res_crit, res_backup, _) = resource_data
                else:
                    res_id, res_name, res_desc, res_category, res_type, res_life, res_format, res_scale, _ = resource_data
                    res_conf = res_users = res_crit = res_backup = "❓ Неизвестно"

                st.subheader("⚡ Моделирование инициирующего события")

                col_event1, col_event2 = st.columns([2, 1])
                with col_event1:
                    event_name = st.text_input(
                        "Описание события",
                        placeholder="Например: Обнаружена критическая уязвимость, утечка данных, изменение законодательства...",
                        key="incident_event"
                    )
                with col_event2:
                    analyze_incident_btn = st.button(
                        "🤖 Анализ события",
                        type="secondary",
                        use_container_width=True,
                        disabled=not event_name
                    )

                if analyze_incident_btn and event_name:
                    with st.spinner("🔍 ИИ анализирует влияние события..."):
                        current_params = {
                            'access_category': REVERSE_ACCESS.get(res_category, "public"),
                            'resource_type': REVERSE_TYPE.get(res_type, "unknown"),
                            'lifecycle': REVERSE_LIFE.get(res_life, "unknown"),
                            'data_format': REVERSE_FORMAT.get(res_format, "unknown"),
                            'usage_scale': REVERSE_SCALE.get(res_scale, "unknown")
                        }
                        analysis = ai.analyze_incident(res_name, res_desc, current_params, event_name)
                        if "error" not in analysis:
                            st.session_state.incident_analysis = analysis
                            st.success("✅ Анализ получен")
                        else:
                            st.error(f"Ошибка: {analysis['error']}")

                if st.session_state.get("incident_analysis"):
                    analysis = st.session_state.incident_analysis
                    with st.expander("🤖 Рекомендации ИИ по изменению рангов", expanded=True):
                        if "summary" in analysis:
                            st.info(f"**Общий вывод:** {analysis['summary']}")

                        if "recommendations" in analysis:
                            st.markdown("**Рекомендуемые изменения рангов:**")
                            crit_names = {
                                'fin': '💰 Финансовый',
                                'oper': '⚙️ Операционный',
                                'jur': '⚖️ Юридический',
                                'rep': '📢 Репутационный',
                                'strat': '🚩 Стратегический'
                            }
                            for crit, name in crit_names.items():
                                if crit in analysis["recommendations"]:
                                    rec = analysis["recommendations"][crit]
                                    change = rec.get('change', '0')
                                    if change.startswith('+'):
                                        change_icon = '🔺'
                                    elif change.startswith('-'):
                                        change_icon = '🔻'
                                    else:
                                        change_icon = '⚪'
                                    st.markdown(f"**{name}:** {change_icon} {change} — {rec.get('reason', '')}")

                            if "law_refs_all" in analysis and analysis["law_refs_all"]:
                                # Исправлено: преобразуем в list безопасно
                                law_refs_list = list(analysis["law_refs_all"]) if isinstance(analysis["law_refs_all"],
                                                                                             (set, list)) else []
                                if law_refs_list:
                                    st.caption("📄 **Источники:** " + ", ".join(law_refs_list[:3]))

                        elif "analysis" in analysis and isinstance(analysis["analysis"], dict):
                            # Старый формат (словарь)
                            for param, data in analysis["analysis"].items():
                                if data.get("should_change"):
                                    st.warning(f"**{param}:** требуется изменение")
                                    st.markdown(f"*Причина:* {data.get('reason', '?')}")
                                    st.markdown("---")
                        else:
                            # Текстовый формат
                            st.markdown(analysis.get("analysis", "Нет подробного анализа"))

                st.markdown("---")
                st.subheader("📊 Переоценка ресурса после события")

                last_eval = db.get_latest_evaluation(selected_res_id)

                if last_eval:
                    current_ranks = {
                        'fin': last_eval[0],
                        'oper': last_eval[1],
                        'jur': last_eval[2],
                        'rep': last_eval[3],
                        'strat': last_eval[4]
                    }

                    st.markdown("**Текущие ранги (можно скорректировать):**")
                    st.markdown("**Текущие ранги (можно скорректировать):**")
                    col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
                    with col_r1:
                        st.metric("💰 Финансовый", f"{current_ranks['fin']}/10")
                    with col_r2:
                        st.metric("⚙️ Операционный", f"{current_ranks['oper']}/10")
                    with col_r3:
                        st.metric("⚖️ Юридический", f"{current_ranks['jur']}/8")
                    with col_r4:
                        st.metric("📢 Репутационный", f"{current_ranks['rep']}/8")
                    with col_r5:
                        st.metric("🚩 Стратегический", f"{current_ranks['strat']}/8")

                    st.markdown("---")
                    st.subheader("📊 Корректировка рангов после события")

                    col_r1, col_r2 = st.columns(2)
                    with col_r1:
                        new_fin = st.slider("💰 Финансовый (1-10)", 1, 10, current_ranks['fin'], key="inc_fin")
                        new_oper = st.slider("⚙️ Операционный (1-10)", 1, 10, current_ranks['oper'], key="inc_oper")
                        new_jur = st.slider("⚖️ Юридический (1-8)", 1, 8, current_ranks['jur'], key="inc_jur")
                    with col_r2:
                        new_rep = st.slider("📢 Репутационный (1-8)", 1, 8, current_ranks['rep'], key="inc_rep")
                        new_strat = st.slider("🚩 Стратегический (1-8)", 1, 8, current_ranks['strat'], key="inc_strat")

                    if st.button("💾 Зафиксировать событие и сохранить", type="primary", width="stretch"):
                        if event_name:
                            new_ranks = {
                                'fin': new_fin,
                                'oper': new_oper,
                                'jur': new_jur,
                                'rep': new_rep,
                                'strat': new_strat
                            }
                            s_scores, total_s = logic.calculate_normalization(new_ranks)
                            final_rank = logic.get_final_rank(total_s)
                            db.save_evaluation(
                                selected_res_id, new_ranks, total_s, final_rank, trigger=event_name
                            )

                            st.toast(f"✅ Событие зафиксировано! Новый ранг: {final_rank}", icon="✅")
                            st.success(f"✅ Событие зафиксировано! Новый ранг: {final_rank}")
                            st.balloons()

                            st.session_state.incident_analysis = None

                            import time

                            time.sleep(1.5)
                            st.rerun()
                        else:
                            st.error("❌ Введите описание события")


# ============================================================================
# ВКЛАДКА 4: БАЗА РЕСУРСОВ И ОТЧЕТЫ
# ============================================================================
with tab4:
    st.markdown("<h2 style='font-size: 2.2rem;'>📚 База информационных ресурсов и отчеты</h2>", unsafe_allow_html=True)
    st.header("📚 База информационных ресурсов и отчеты")

    resources = db.get_all_resources_full()

    if resources:
        has_new_fields = len(resources[0]) > 5 if resources else False

        if has_new_fields:
            df_res = pd.DataFrame(
                resources,
                columns=["ID", "Название", "Категория", "Описание", "Дата создания",
                         "Конфиденциальность", "Пользователи", "Критичность", "Бэкап"]
            )
        else:
            df_res = pd.DataFrame(
                resources,
                columns=["ID", "Название", "Категория", "Описание", "Дата создания"]
            )

        st.dataframe(df_res, use_container_width=True)

        st.subheader("📊 Статистика")
        stats = db.get_stats()

        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("Всего ресурсов", stats.get('total_resources', 0))
        with col_stat2:
            st.metric("Всего оценок", stats.get('total_evaluations', 0))
        with col_stat3:
            st.metric("Средний ранг", stats.get('avg_final_rank', 0))
        with col_stat4:
            st.metric("Последнее обновление", datetime.now().strftime("%d.%m.%Y"))

        cat_stats = db.get_resources_by_category()
        if cat_stats:
            st.subheader("📊 Распределение по категориям")
            df_cat = pd.DataFrame(cat_stats, columns=["Категория", "Количество"])
            st.bar_chart(df_cat.set_index("Категория"))

        st.markdown("---")
        st.subheader("🔍 Детальная информация о ресурсе")

        res_for_detail = st.selectbox(
            "Выберите ресурс",
            options=df_res["ID"].tolist(),
            format_func=lambda x: f"{x}: {df_res[df_res['ID'] == x]['Название'].values[0]}",
            key="res_for_detail"
        )

        if res_for_detail:
            history = db.get_evaluation_history(res_for_detail)
            if history:
                df_detail = pd.DataFrame(
                    history,
                    columns=["Дата", "Событие", "Ранг", "Фин", "Опер", "Юр", "Реп", "Страт", "S∑", "Детали"]
                )
                display_cols = ["Дата", "Событие", "Ранг", "Фин", "Опер", "Юр", "Реп", "Страт", "S∑"]
                st.dataframe(df_detail[display_cols], use_container_width=True)

                csv = df_detail[display_cols].to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Скачать историю (CSV)",
                    csv,
                    f"resource_{res_for_detail}_history.csv",
                    "text/csv",
                    use_container_width=True
                )

                if df_detail.iloc[-1]["Детали"]:
                    with st.expander("📋 Детали последнего расчета"):
                        try:
                            details = json.loads(df_detail.iloc[-1]["Детали"])
                            st.json(details)
                        except:
                            st.write(df_detail.iloc[-1]["Детали"])
            else:
                st.info("ℹ️ Для этого ресурса еще нет оценок.")

        if st.button("🔄 Оптимизировать базу данных"):
            db.vacuum_db()
            st.success("✅ База данных оптимизирована")
    else:
        st.info("ℹ️ База данных пуста")


# ============================================================================
# ПОДВАЛ
# ============================================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 10px;'>
        © 2025 Система поддержки принятия решений для оценки динамики ценности информационных ресурсов<br>
        Разработано в рамках ВКР по специальности 10.05.04
    </div>
    """,
    unsafe_allow_html=True
)