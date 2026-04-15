import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import modules.ai_analyst as ai
import database as db
import logic
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
import tempfile
# Настройка страницы (ТОЛЬКО ОДИН РАЗ!)
st.set_page_config(
    page_title="СППР Оценка динамики ценности ИР",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
/* ========== РАСШИРЯЕМ КОНТЕЙНЕР ========== */
.block-container {
    max-width: 1400px !important;
    padding: 2rem !important;
}

/* ========== ОСНОВНОЙ ТЕКСТ - БОЛЬШИЕ БУКВЫ ========== */
.stMarkdown, p, li, div, span {
    font-size: 22px !important;
    line-height: 1.5 !important;
}

/* ========== ЛЕЙБЛЫ (НАДПИСИ НАД ПОЛЯМИ) ========== */
label, .stTextInput label, .stTextArea label, .stSelectbox label {
    font-size: 22px !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
}

/* ========== SELECTBOX - УВЕЛИЧИВАЕМ ВЫСОТУ ========== */
div[data-baseweb="select"] {
    width: 100% !important;
    min-width: 250px !important;
}

/* Основное поле выбора - УВЕЛИЧЕННАЯ ВЫСОТА */
div[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border: 2px solid #cccccc !important;
    border-radius: 8px !important;
    padding: 15px 12px !important;
    min-height: 65px !important;
    height: auto !important;
}

/* Текст в поле выбора (что выбрано) */
div[data-baseweb="select"] div[aria-selected="true"] {
    font-size: 20px !important;
    color: #000000 !important;
    white-space: normal !important;
    word-break: break-word !important;
    overflow: visible !important;
    text-overflow: clip !important;
    line-height: 1.4 !important;
    min-height: 30px !important;
    display: block !important;
}

/* Все спаны внутри select */
div[data-baseweb="select"] span {
    font-size: 20px !important;
    color: #000000 !important;
    white-space: normal !important;
    word-break: break-word !important;
    line-height: 1.4 !important;
}

/* Выпадающий список */
div[role="listbox"] {
    background-color: #ffffff !important;
    border: 1px solid #cccccc !important;
    border-radius: 8px !important;
    min-width: 350px !important;
    max-width: 500px !important;
    z-index: 9999 !important;
}

/* Элементы выпадающего списка */
div[role="listbox"] div[role="option"] {
    font-size: 18px !important;
    padding: 12px 15px !important;
    color: #000000 !important;
    white-space: normal !important;
    word-break: break-word !important;
    overflow: visible !important;
    text-overflow: clip !important;
    border-bottom: 1px solid #eeeeee !important;
    min-height: 50px !important;
}

/* Убираем троеточие везде */
.stSelectbox [class*="truncate"],
.stSelectbox [class*="ellipsis"],
.stSelectbox [class*="overflow"] {
    text-overflow: clip !important;
    white-space: normal !important;
    overflow: visible !important;
}

/* Исправляем контейнер выбранного значения */
.stSelectbox .st-bb {
    white-space: normal !important;
    word-break: break-word !important;
    overflow: visible !important;
}

/* ========== ТАБЫ В 2 РЯДА ========== */
.stTabs {
    margin-top: 20px;
}

.stTabs [data-baseweb="tab-list"] {
    display: grid !important;
    grid-template-columns: repeat(2, 1fr) !important;
    gap: 10px !important;
    background-color: transparent !important;
    padding: 0 !important;
    margin-bottom: 20px !important;
}

.stTabs [data-baseweb="tab"] {
    font-size: 18px !important;
    padding: 12px 16px !important;
    background-color: #e0e0e0 !important;
    border-radius: 10px !important;
    text-align: center !important;
    white-space: normal !important;
    word-break: break-word !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
}

.stTabs [aria-selected="true"] {
    background-color: #1b5e20 !important;
    color: white !important;
}

.stTabs [data-baseweb="tab"]:hover {
    background-color: #c0c0c0 !important;
}

/* ========== INPUT ПОЛЯ ========== */
.stTextInput input, .stTextArea textarea {
    font-size: 20px !important;
    padding: 12px !important;
    border-radius: 8px !important;
    min-height: 55px !important;
}
::placeholder {
    font-size: 18px !important;
}

/* ========== КНОПКИ ========== */
.stButton button {
    font-size: 20px !important;
    padding: 12px 24px !important;
    border-radius: 10px !important;
    background-color: #4CAF50 !important;
    color: white !important;
    font-weight: 600 !important;
}
.stButton button:hover {
    background-color: #45a049 !important;
}

/* ========== МЕТРИКИ ========== */
[data-testid="stMetricValue"] {
    font-size: 32px !important;
    font-weight: 800 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 18px !important;
}

/* ========== ТАБЛИЦЫ ========== */
.stTable td, .stTable th, .dataframe td, .dataframe th {
    font-size: 16px !important;
    padding: 10px !important;
}

/* ========== EXPANDER ========== */
.streamlit-expanderHeader {
    font-size: 20px !important;
    font-weight: 600 !important;
}

/* ========== ИНФО БЛОКИ ========== */
.stInfo, .stSuccess, .stWarning, .stError {
    font-size: 18px !important;
    padding: 12px !important;
    border-radius: 10px !important;
}

/* ========== КАРТОЧКИ ========== */
.result-card p {
    font-size: 28px !important;
}
.risk-card span {
    font-size: 24px !important;
}
.risk-card strong {
    font-size: 16px !important;
}

/* ========== СЛАЙДЕРЫ ========== */
.stSlider label {
    font-size: 18px !important;
}

/* ========== КОЛОНКИ ========== */
.row-widget.stColumns {
    flex-wrap: wrap !important;
}
.stColumn {
    min-width: 280px !important;
    padding: 0 10px !important;
}

/* ========== ПОДВАЛ ========== */
footer {
    font-size: 14px !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<script>
(function() {
    function fixSelectBoxes() {
        // Находим все выпадающие списки
        const selects = document.querySelectorAll('[data-baseweb="select"]');
        selects.forEach(select => {
            // Увеличиваем высоту контейнера
            const container = select.querySelector('div[aria-selected="true"]');
            if (container) {
                container.style.whiteSpace = 'normal';
                container.style.wordBreak = 'break-word';
                container.style.overflow = 'visible';
                container.style.textOverflow = 'clip';
                container.style.lineHeight = '1.4';
                container.style.minHeight = '40px';
                container.style.display = 'block';
            }

            // Исправляем родительский контейнер
            const parentDiv = select.querySelector('div');
            if (parentDiv) {
                parentDiv.style.minHeight = '65px';
                parentDiv.style.height = 'auto';
            }
        });

        // Наблюдаем за изменениями
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    const newSelects = document.querySelectorAll('[data-baseweb="select"]');
                    newSelects.forEach(select => {
                        const container = select.querySelector('div[aria-selected="true"]');
                        if (container) {
                            container.style.whiteSpace = 'normal';
                            container.style.wordBreak = 'break-word';
                            container.style.overflow = 'visible';
                            container.style.minHeight = '40px';
                        }
                        const parentDiv = select.querySelector('div');
                        if (parentDiv) {
                            parentDiv.style.minHeight = '65px';
                            parentDiv.style.height = 'auto';
                        }
                    });
                }
            });
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixSelectBoxes);
    } else {
        fixSelectBoxes();
    }
})();
</script>
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
    Гарантированно возвращает все 9 параметров
    """
    desc_lower = resource_desc.lower()
    import re

    # Если suggestions не словарь или None, создаём пустой
    if not suggestions or not isinstance(suggestions, dict):
        suggestions = {}

    # =========================================================================
    # 0. ГАРАНТИРОВАННОЕ ЗАПОЛНЕНИЕ ВСЕХ 9 ПАРАМЕТРОВ (заглушки)
    # =========================================================================
    all_params = ["access_category", "resource_type", "lifecycle", "data_format",
                  "usage_scale", "confidentiality", "users_count",
                  "business_criticality", "backup"]

    # Сначала заполняем значениями по умолчанию (если параметра нет или он unknown)
    for param in all_params:
        if param not in suggestions or not suggestions[param] or (
                isinstance(suggestions[param], dict) and suggestions[param].get("value") == "unknown"):

            if param == "access_category":
                suggestions[param] = {"value": "internal", "reason": "Внутренняя информация (будет уточнено)"}
            elif param == "resource_type":
                suggestions[param] = {"value": "database", "reason": "База данных (тип определён по умолчанию)"}
            elif param == "lifecycle":
                suggestions[param] = {"value": "medium_term", "reason": "Среднесрочный цикл (определён по умолчанию)"}
            elif param == "data_format":
                suggestions[param] = {"value": "structured", "reason": "Структурированные данные"}
            elif param == "usage_scale":
                suggestions[param] = {"value": "enterprise", "reason": "Масштаб предприятия"}
            elif param == "confidentiality":
                suggestions[param] = {"value": "confidential", "reason": "Конфиденциальная информация"}
            elif param == "users_count":
                suggestions[param] = {"value": "10000+", "reason": "Много пользователей"}
            elif param == "business_criticality":
                suggestions[param] = {"value": "high", "reason": "Высокая важность для бизнеса"}
            elif param == "backup":
                suggestions[param] = {"value": "weekly", "reason": "Регулярное резервное копирование"}

    # =========================================================================
    # 1. УМНОЕ ОПРЕДЕЛЕНИЕ КАТЕГОРИИ ДОСТУПА (из описания)
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
    database_keywords = [
        'база данн', 'бд', 'хранилищ', 'таблиц', 'sql', 'postgresql',
        'oracle', 'mysql', 'mongodb', 'электронн таблиц', 'реестр',
        'каталог', 'справочник', 'журнал', 'регистр'
    ]

    software_keywords = [
        'программ', 'приложени', 'систем', 'модул', 'скрипт', 'алгоритм',
        'сервис', 'платформа', 'интерфейс', 'api', 'веб', 'мобильн'
    ]

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
    # 3. ОПРЕДЕЛЕНИЕ КОЛИЧЕСТВА ПОЛЬЗОВАТЕЛЕЙ
    # =========================================================================
    def extract_numbers_with_context(text, keywords):
        results = []
        for keyword in keywords:
            pattern_before = r'(\d{1,3}(?:[\s]?\d{3})*)\s*' + keyword
            matches_before = re.findall(pattern_before, text)
            for match in matches_before:
                clean_num = match.replace(' ', '')
                try:
                    results.append(int(clean_num))
                except:
                    pass

            pattern_after = keyword + r'\s*(\d{1,3}(?:[\s]?\d{3})*)'
            matches_after = re.findall(pattern_after, text)
            for match in matches_after:
                clean_num = match.replace(' ', '')
                try:
                    results.append(int(clean_num))
                except:
                    pass

            pattern_plus = r'(\d{1,3}(?:[\s]?\d{3})*)\+\s*' + keyword
            matches_plus = re.findall(pattern_plus, text)
            for match in matches_plus:
                clean_num = match.replace(' ', '')
                try:
                    results.append(int(clean_num))
                except:
                    pass
        return results

    user_keywords = [
        'сотрудник', 'работник', 'персонал', 'человек', 'пользовател',
        'клиент', 'покупател', 'врач', 'медсестр', 'медицинск', 'учител',
        'студент', 'учащийся', 'сотр', 'чел'
    ]

    all_numbers = extract_numbers_with_context(desc_lower, user_keywords)

    if not all_numbers:
        any_numbers = re.findall(r'(\d{1,6})', desc_lower)
        for num_str in any_numbers:
            try:
                num = int(num_str)
                position = desc_lower.find(num_str)
                context = desc_lower[max(0, position - 40):min(len(desc_lower), position + 40)]
                if any(keyword in context for keyword in user_keywords):
                    all_numbers.append(num)
            except:
                pass

    if all_numbers:
        max_users = max(all_numbers)
        if max_users >= 10000:
            suggestions["users_count"] = {"value": "10000+", "reason": f"Более {max_users} пользователей"}
        elif max_users >= 1000:
            suggestions["users_count"] = {"value": "1001-10000", "reason": f"Около {max_users} пользователей"}
        elif max_users >= 100:
            suggestions["users_count"] = {"value": "101-1000", "reason": f"Около {max_users} пользователей"}
        elif max_users >= 11:
            suggestions["users_count"] = {"value": "11-100", "reason": f"Около {max_users} пользователей"}
        elif max_users >= 1:
            suggestions["users_count"] = {"value": "1-10", "reason": f"Около {max_users} пользователей"}

    # =========================================================================
    # 4. ОПРЕДЕЛЕНИЕ ФОРМАТА ДАННЫХ
    # =========================================================================
    structured_keywords = [
        'база данн', 'бд', 'таблиц', 'sql', 'postgresql', 'oracle', 'mysql',
        'реестр', 'каталог', 'справочник', 'журнал', 'регистр', 'json', 'xml',
        'структурирован', 'электронн таблиц', 'excel'
    ]
    source_keywords = ['исходный код', 'программ', 'скрипт', 'алгоритм', 'разработк', 'репозиторий', 'git', 'svn']
    text_keywords = ['документ', 'текст', 'файл', 'отчёт', 'письмо', 'инструкци', 'регламент', 'положени', 'приказ']

    if any(word in desc_lower for word in structured_keywords):
        suggestions["data_format"] = {"value": "structured", "reason": "Данные структурированы и организованы"}
    elif any(word in desc_lower for word in source_keywords):
        suggestions["data_format"] = {"value": "source_code", "reason": "Ресурс содержит исходный код или скрипты"}
    elif any(word in desc_lower for word in text_keywords):
        suggestions["data_format"] = {"value": "text", "reason": "Данные представлены в виде текстовых документов"}

    # =========================================================================
    # 5. ОПРЕДЕЛЕНИЕ ЖИЗНЕННОГО ЦИКЛА
    # =========================================================================
    year_pattern = r'(\d+)\s*лет'
    years_match = re.findall(year_pattern, desc_lower)
    if years_match:
        max_years = max(int(y) for y in years_match)
        if max_years >= 3:
            suggestions["lifecycle"] = {"value": "long_term",
                                        "reason": f"Срок хранения данных составляет {max_years} лет"}
        elif max_years >= 1:
            suggestions["lifecycle"] = {"value": "medium_term",
                                        "reason": f"Срок хранения данных составляет {max_years} года"}
    else:
        if any(word in desc_lower for word in ['долгосроч', 'длительн', 'многолет', 'архив']):
            suggestions["lifecycle"] = {"value": "long_term", "reason": "Ресурс имеет долгосрочный характер хранения"}
        elif any(word in desc_lower for word in ['краткосроч', 'быстро устарев']):
            suggestions["lifecycle"] = {"value": "short_term", "reason": "Ресурс имеет краткосрочный характер"}

    # =========================================================================
    # 6. ОПРЕДЕЛЕНИЕ КРИТИЧНОСТИ
    # =========================================================================
    critical_keywords = ['критич', 'остановк', 'невозможн', 'теряет', 'без ресурс', 'простой', 'аварий',
                         'жизненно важн', 'ключевой']
    if any(word in desc_lower for word in critical_keywords):
        suggestions["business_criticality"] = {"value": "critical",
                                               "reason": "Ресурс критически важен для бизнес-процессов"}
    elif any(word in desc_lower for word in ['важн', 'значим', 'основн']):
        suggestions["business_criticality"] = {"value": "high", "reason": "Ресурс имеет высокую важность для бизнеса"}

    # =========================================================================
    # 7. ОПРЕДЕЛЕНИЕ БЭКАПА
    # =========================================================================
    if any(word in desc_lower for word in ['ежедневн', 'каждый день', 'daily']):
        suggestions["backup"] = {"value": "daily", "reason": "Резервное копирование выполняется ежедневно"}
    elif any(word in desc_lower for word in ['еженедельн', 'раз в неделю', 'weekly']):
        suggestions["backup"] = {"value": "weekly", "reason": "Резервное копирование выполняется еженедельно"}
    elif any(word in desc_lower for word in ['ежемесячн', 'раз в месяц', 'monthly']):
        suggestions["backup"] = {"value": "monthly", "reason": "Резервное копирование выполняется ежемесячно"}
    elif any(word in desc_lower for word in ['нет бэкап', 'отсутству', 'не производит']):
        suggestions["backup"] = {"value": "none", "reason": "Резервное копирование отсутствует"}

    # =========================================================================
    # 8. ОПРЕДЕЛЕНИЕ МАСШТАБА
    # =========================================================================
    if any(word in desc_lower for word in ['все подразделени', 'всей организации', 'все предприяти', 'корпоративн']):
        suggestions["usage_scale"] = {"value": "enterprise",
                                      "reason": "Ресурс используется во всех подразделениях предприятия"}
    elif any(word in desc_lower for word in ['отдел', 'департамент', 'подразделени']):
        suggestions["usage_scale"] = {"value": "department", "reason": "Ресурс используется на уровне отдела"}
    elif any(word in desc_lower for word in ['рабочее место', 'локальн', 'отдельн сотрудник']):
        suggestions["usage_scale"] = {"value": "local", "reason": "Ресурс используется локально"}

    # =========================================================================
    # 9. КОРРЕКТИРОВКИ (если ИИ ошибся)
    # =========================================================================
    # Корректировка типа ресурса
    if suggestions.get("resource_type", {}).get("value") == "software":
        db_indicators = ['данные о', 'содержит данные', 'хранит', 'клиентах', 'заказах', 'база данн', 'бд']
        if any(word in desc_lower for word in db_indicators):
            suggestions["resource_type"] = {
                "value": "database",
                "reason": "Ресурс является базой данных, содержащей структурированную информацию"
            }

    # Корректировка формата данных
    if suggestions.get("data_format", {}).get("value") == "text":
        structured_indicators = ['клиентах', 'заказах', 'данные о', 'база', 'таблиц', 'структурирован']
        if any(word in desc_lower for word in structured_indicators):
            suggestions["data_format"] = {
                "value": "structured",
                "reason": "Данные структурированы и организованы в базе данных"
            }

    # Корректировка конфиденциальности
    if suggestions.get("confidentiality", {}).get("value") in ["secret", "top_secret"]:
        if not any(word in desc_lower for word in state_keywords):
            suggestions["confidentiality"] = {
                "value": "confidential",
                "reason": "Информация является конфиденциальной, но не составляет государственную тайну"
            }

    # Финальная проверка: все 9 параметров точно есть
    for param in all_params:
        if param not in suggestions or not isinstance(suggestions[param], dict):
            # Если вдруг чего-то не хватаем — ставим дефолт
            defaults = {
                "access_category": {"value": "internal", "reason": "Значение по умолчанию"},
                "resource_type": {"value": "database", "reason": "Значение по умолчанию"},
                "lifecycle": {"value": "medium_term", "reason": "Значение по умолчанию"},
                "data_format": {"value": "structured", "reason": "Значение по умолчанию"},
                "usage_scale": {"value": "enterprise", "reason": "Значение по умолчанию"},
                "confidentiality": {"value": "confidential", "reason": "Значение по умолчанию"},
                "users_count": {"value": "10000+", "reason": "Значение по умолчанию"},
                "business_criticality": {"value": "high", "reason": "Значение по умолчанию"},
                "backup": {"value": "weekly", "reason": "Значение по умолчанию"}
            }
            suggestions[param] = defaults[param]

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

                # ОТЛАДКА: выводим в консоль, что вернул ИИ
                print("=== AI RESPONSE ===")
                print(analysis)
                print("===================")

                if "error" not in analysis:
                    suggestions = analysis.get("suggestions", {})
                    print("Suggestions before validate:", suggestions.keys())

                    suggestions = validate_ai_suggestions(suggestions, resource_desc)

                    print("Suggestions after validate:", suggestions.keys())
                    for k, v in suggestions.items():
                        print(f"  {k}: {v}")

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

                # Все параметры идут вертикально вниз в нужном порядке
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

                if "data_format" in suggestions:  # Формат данных ПОСЛЕ жизненного цикла
                    df = suggestions["data_format"]
                    st.info(
                        f"**Формат данных:** {RUSSIAN_FORMAT.get(df.get('value', 'unknown'), df.get('value', 'unknown'))}\n\n*{df.get('reason', '')}*")

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

                if "business_criticality" in suggestions:  # Критичность ПОСЛЕ количества пользователей
                    crit = suggestions["business_criticality"]
                    st.info(
                        f"**Критичность:** {RUSSIAN_CRITICALITY.get(crit.get('value', 'unknown'), crit.get('value', 'unknown'))}\n\n*{crit.get('reason', '')}*")

                if "backup" in suggestions:
                    backup = suggestions["backup"]
                    st.info(
                        f"**Резервное копирование:** {RUSSIAN_BACKUP.get(backup.get('value', 'unknown'), backup.get('value', 'unknown'))}\n\n*{backup.get('reason', '')}*")

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
        col_a1, col_a2 = st.columns([1, 1])

        # Добавь после этого:
        st.markdown("""
        <style>
        .stColumn {
            min-width: 320px !important;
            padding-right: 15px !important;
        }
        </style>
        """, unsafe_allow_html=True)

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
                        # ИСПРАВЛЕНО: используем result['total_s']
                        display_metric("📈 Интегральный S∑", f"{result['total_s']:.3f}")
                    with col_i2:
                        display_metric("🏆 Итоговый ранг", str(result['final_rank']))
                    with col_i3:
                        display_metric("🛡️ Уровень защиты", result['protection_level'])

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
    st.markdown("<h2 style='font-size: 2.2rem; margin-bottom: 1rem;'>⚡ Анализ динамики ценности при инцидентах</h2>", unsafe_allow_html=True)

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
            st.subheader("📈 Динамика изменения ценности ресурса")

            df_history = pd.DataFrame(
                history,
                columns=["Дата", "Событие", "Ранг", "Фин", "Опер", "Юр", "Реп", "Страт", "S∑", "Детали"]
            )

            if len(df_history) > 1:
                import plotly.express as px

                # Создаём порядковый номер оценки (1, 2, 3...)
                df_history_copy = df_history.copy()
                df_history_copy["№ оценки"] = range(1, len(df_history_copy) + 1)

                # Добавляем столбец с датой для отображения при наведении
                df_history_copy["Дата и время"] = df_history_copy["Дата"]

                fig = px.line(
                    df_history_copy,
                    x="№ оценки",
                    y="Ранг",
                    title="📈 Динамика изменения ценности ресурса",
                    markers=True,
                    text="Ранг",
                    labels={"№ оценки": "Номер оценки (по порядку)", "Ранг": "Итоговый ранг (1-9)"}
                )

                # Добавляем подписи точек
                fig.update_traces(textposition="top center", textfont_size=14)

                # Настройка осей
                fig.update_yaxes(range=[0.5, 9.5], dtick=1, title_font_size=16)
                fig.update_xaxes(title_font_size=16, tickmode='linear', dtick=1)

                # Настройка внешнего вида
                fig.update_layout(
                    font=dict(size=14),
                    title_font=dict(size=20),
                    hovermode='closest',
                    showlegend=False
                )

                # Добавляем информацию о датах при наведении
                fig.update_traces(
                    hovertemplate='<b>№ оценки: %{x}</b><br>Ранг: %{y}<br>Дата: %{customdata}<extra></extra>',
                    customdata=df_history_copy["Дата и время"]
                )

                st.plotly_chart(fig, use_container_width=True)

                # Дополнительная таблица с соответствием номеров и дат
                with st.expander("📅 Соответствие номера оценки и даты"):
                    date_mapping = df_history_copy[["№ оценки", "Дата", "Событие", "Ранг"]]
                    st.dataframe(date_mapping, use_container_width=True)

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

                # ========== КНОПКИ ЭКСПОРТА ==========
                col_export1, col_export2 = st.columns(2)

                with col_export1:
                    csv = df_detail[display_cols].to_csv(index=False).encode('utf-8-sig')
                    st.download_button(
                        "📥 Скачать историю (CSV)",
                        csv,
                        f"resource_{res_for_detail}_history.csv",
                        "text/csv",
                        use_container_width=True
                    )

                with col_export2:
                    try:
                        import io
                        import matplotlib.pyplot as plt
                        from matplotlib import rcParams
                        from reportlab.lib.pagesizes import A4
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
                        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                        from reportlab.lib.units import mm
                        from reportlab.lib import colors
                        from reportlab.pdfbase import pdfmetrics
                        from reportlab.pdfbase.ttfonts import TTFont

                        # Шрифт
                        font_path = os.path.join(os.path.dirname(__file__), "DejaVuSans.ttf")
                        if not os.path.exists(font_path):
                            font_path = os.path.join(os.path.dirname(__file__), "DejaVuSansCondensed-Bold.ttf")

                        if os.path.exists(font_path):
                            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
                            font_name = 'DejaVu'
                        else:
                            font_name = 'Helvetica'

                        # График
                        rcParams['font.family'] = 'sans-serif'
                        rcParams['font.sans-serif'] = ['DejaVu Sans']

                        fig, ax = plt.subplots(figsize=(10, 5))
                        x_vals = range(1, len(df_detail) + 1)
                        y_vals = df_detail['Ранг'].values

                        ax.plot(x_vals, y_vals, marker='o', linewidth=2, markersize=8, color='#1b5e20')
                        ax.fill_between(x_vals, y_vals, alpha=0.3, color='#4CAF50')
                        ax.set_xlabel('Номер оценки', fontsize=12)
                        ax.set_ylabel('Итоговый ранг (1-9)', fontsize=12)
                        ax.set_title('Динамика изменения ценности ресурса', fontsize=14, fontweight='bold')
                        ax.set_ylim(0.5, 9.5)
                        ax.set_yticks(range(1, 10))
                        ax.grid(True, alpha=0.3)

                        for i, (x, y) in enumerate(zip(x_vals, y_vals)):
                            ax.annotate(str(y), (x, y), textcoords="offset points", xytext=(0, 10), ha='center',
                                        fontsize=9)

                        plt.tight_layout()

                        import tempfile

                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                            plt.savefig(tmp.name, dpi=150, bbox_inches='tight')
                            plot_path = tmp.name
                        plt.close()

                        # PDF
                        buffer = io.BytesIO()
                        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm,
                                                topMargin=20 * mm, bottomMargin=15 * mm)
                        styles = getSampleStyleSheet()

                        title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], fontName=font_name,
                                                     fontSize=18, alignment=1, spaceAfter=20)
                        heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontName=font_name,
                                                       fontSize=14, spaceAfter=10, textColor=colors.darkgreen)
                        normal_style = ParagraphStyle('NormalStyle', parent=styles['Normal'], fontName=font_name,
                                                      fontSize=9, leading=12)

                        story = []

                        # Заголовок
                        res_info = df_res[df_res['ID'] == res_for_detail].iloc[0]
                        story.append(Paragraph(f"Отчёт по ресурсу №{res_for_detail}", title_style))
                        story.append(Spacer(1, 5 * mm))

                        # Информация о ресурсе
                        info_text = f"""
                        <b>Название:</b> {res_info.get('Название', 'Н/Д')}<br/>
                        <b>Категория доступа:</b> {res_info.get('Категория', 'Н/Д')}<br/>
                        <b>Дата создания:</b> {res_info.get('Дата создания', 'Н/Д')}<br/>
                        """
                        if has_new_fields:
                            info_text += f"""
                            <b>Конфиденциальность:</b> {res_info.get('Конфиденциальность', 'Н/Д')}<br/>
                            <b>Количество пользователей:</b> {res_info.get('Пользователи', 'Н/Д')}<br/>
                            <b>Критичность:</b> {res_info.get('Критичность', 'Н/Д')}<br/>
                            <b>Резервное копирование:</b> {res_info.get('Бэкап', 'Н/Д')}<br/>
                            """
                        story.append(Paragraph(info_text, normal_style))
                        story.append(Spacer(1, 10 * mm))

                        # График
                        story.append(Paragraph("Динамика изменения ценности", heading_style))
                        story.append(Spacer(1, 5 * mm))
                        story.append(Image(plot_path, width=160 * mm, height=80 * mm))
                        story.append(Spacer(1, 10 * mm))

                        # ========== ТАБЛИЦА С ПЕРЕНОСОМ ТЕКСТА ==========
                        story.append(Paragraph("История оценок", heading_style))
                        story.append(Spacer(1, 5 * mm))

                        # Создаём таблицу с Paragraph для колонки "Событие"
                        table_data = [["№", "Дата", "Событие", "Р", "Ф", "О", "Ю", "Рп", "С"]]

                        for idx, row in df_detail.iterrows():
                            # Ключевое: оборачиваем событие в Paragraph для автоматического переноса
                            event_para = Paragraph(row['Событие'], normal_style)
                            table_data.append([
                                str(idx + 1),
                                row['Дата'][:16],
                                event_para,
                                str(row['Ранг']),
                                str(row['Фин']),
                                str(row['Опер']),
                                str(row['Юр']),
                                str(row['Реп']),
                                str(row['Страт'])
                            ])

                        # Ширины колонок
                        col_widths = [10 * mm, 35 * mm, 85 * mm, 8 * mm, 8 * mm, 8 * mm, 8 * mm, 8 * mm, 8 * mm]

                        table = Table(table_data, colWidths=col_widths, repeatRows=1)
                        table.setStyle(TableStyle([
                            ('FONTNAME', (0, 0), (-1, -1), font_name),
                            ('FONTSIZE', (0, 0), (-1, -1), 8),
                            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                        ]))
                        story.append(table)
                        story.append(Spacer(1, 10 * mm))

                        # Статистика
                        story.append(Paragraph("Статистика", heading_style))
                        first_rank = df_detail['Ранг'].iloc[0]
                        last_rank = df_detail['Ранг'].iloc[-1]
                        change = last_rank - first_rank
                        change_text = f"+{change}" if change >= 0 else f"{change}"

                        stats_text = f"""
                        <b>Всего оценок:</b> {len(df_detail)}<br/>
                        <b>Минимальный ранг:</b> {df_detail['Ранг'].min()}<br/>
                        <b>Максимальный ранг:</b> {df_detail['Ранг'].max()}<br/>
                        <b>Средний ранг:</b> {df_detail['Ранг'].mean():.2f}<br/>
                        <b>Изменение ранга:</b> {change_text} (с {first_rank} до {last_rank})
                        """
                        story.append(Paragraph(stats_text, normal_style))

                        doc.build(story)
                        buffer.seek(0)

                        os.unlink(plot_path)

                        st.download_button(
                            "📥 Скачать отчёт (PDF)",
                            buffer,
                            f"resource_{res_for_detail}_report.pdf",
                            "application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.warning(f"PDF экспорт временно недоступен: {e}")
                        st.info("Для PDF экспорта выполните: pip install reportlab matplotlib")

                if df_detail.iloc[-1]["Детали"]:
                    with st.expander("📋 Детали последнего расчета"):
                        try:
                            details = json.loads(df_detail.iloc[-1]["Детали"])
                            st.json(details)
                        except:
                            st.write(df_detail.iloc[-1]["Детали"])
            else:
                st.info("ℹ️ Для этого ресурса еще нет оценок.")

        if st.button("🔄 Оптимизировать базу данных", use_container_width=True):
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
        Разработано в рамках ВКР по специальности 10.03.01
    </div>
    """,
    unsafe_allow_html=True
)