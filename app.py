# app.py (ПОЛНАЯ ФИНАЛЬНАЯ ВЕРСИЯ)
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import modules.ai_analyst as ai
import database as db
import logic

# Настройка страницы
st.set_page_config(
    page_title="СППР Оценка динамики ценности ИР",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================================
# ИНИЦИАЛИЗАЦИЯ СОСТОЯНИЯ СЕССИИ
# ============================================================================
def init_session_state():
    """Инициализация всех переменных состояния сессии"""

    # Состояние для вкладки 1
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

        # Состояние для вкладки 2
        if "selected_resource_for_analysis" not in st.session_state:
            st.session_state.selected_resource_for_analysis = None
        if "calculation_explanation" not in st.session_state:
            st.session_state.calculation_explanation = None
        if "current_calculation" not in st.session_state:
            st.session_state.current_calculation = None
        if "calculation_result" not in st.session_state:  # ← добавить эту строку
            st.session_state.calculation_result = None

    # Состояние для вкладки 3
    if "incident_analysis" not in st.session_state:
        st.session_state.incident_analysis = None


init_session_state()

# ============================================================================
# СЛОВАРИ ДЛЯ ПЕРЕВОДА (ВСЕ ПАРАМЕТРЫ)
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

# НОВЫЕ ПАРАМЕТРЫ
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

# Обратные словари для преобразования русских названий в ключи
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
# ЗАГОЛОВОК И ОПИСАНИЕ МЕТОДИКИ
# ============================================================================
st.title("🛡️ Система поддержки принятия решений для оценки динамики ценности информационных ресурсов")
st.markdown("---")

with st.expander("📚 О методике оценки (Глава 7)", expanded=False):
    st.markdown("""
    ### Математическая модель оценки ценности ИР

    **Формула расчета частного ранга:**
    $R_{критерий} = R_{base} \\times \\prod K_i$

    **Группа А (Критические критерии, шкала 1-10):**
    - **Финансовый ущерб (fin)** - прямые и косвенные потери
    - **Операционный сбой (oper)** - влияние на бизнес-процессы

    **Группа Б (Качественные критерии, шкала 1-8):**
    - **Юридический риск (jur)** - ответственность по НПА
    - **Репутационный ущерб (rep)** - имиджевые потери
    - **Стратегический ущерб (strat)** - влияние на развитие

    **Коэффициенты влияния:**
    - Тип ресурса (K_type): 1.0-1.25
    - Жизненный цикл (K_life): 1.0-1.20
    - Формат данных (K_format): 1.0-1.25
    - Масштаб (K_scale): 1.0-1.20
    - Конфиденциальность (K_conf): 1.0-1.40
    - Количество пользователей (K_users): 1.0-1.20
    - Критичность для бизнеса (K_business): 1.0-1.30
    - Резервное копирование (K_backup): 0.9-1.20

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
with tab1:
    st.header("Регистрация нового информационного ресурса")

    # Основная информация
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Исходные данные")

        resource_name = st.text_input(
            "Название ресурса *",
            placeholder="Например: Медицинская информационная система",
            key="input_name"
        )

        resource_desc = st.text_area(
            "Описание ресурса",
            placeholder="Опишите назначение, содержание, кто работает с ресурсом, срок хранения, формат данных, количество пользователей...",
            height=200,
            key="input_desc"
        )

        # Кнопка запроса к ИИ
        col_ai_btn, col_ai_status = st.columns([1, 2])
        with col_ai_btn:
            ai_request_btn = st.button(
                "🤖 Запросить рекомендации ИИ",
                type="secondary",
                use_container_width=True,
                disabled=not (resource_name and resource_desc)
            )
        with col_ai_status:
            if st.session_state.ai_suggestions:
                st.success("✅ Рекомендации получены")
            else:
                st.info("⏳ ИИ проанализирует описание и найдет связи с нормативными документами")

        # Обработка запроса к ИИ
        if ai_request_btn and resource_name and resource_desc:
            with st.spinner("🔍 ИИ анализирует описание и нормативные документы..."):
                analysis = ai.suggest_parameters(resource_name, resource_desc)

                if "error" not in analysis:
                    st.session_state.ai_suggestions = analysis.get("suggestions", {})
                    st.session_state.ai_law_refs = analysis.get("law_refs", [])
                    st.session_state.ai_summary = analysis.get("summary", "")
                    st.session_state.resource_saved = False
                    st.rerun()
                else:
                    st.error(f"Ошибка при анализе: {analysis['error']}")


        # Отображение рекомендаций ИИ (замените этот блок в app.py)
        if st.session_state.ai_suggestions:
            with st.expander("🤖 Рекомендации ИИ-ассистента", expanded=True):
                if st.session_state.ai_summary:
                    st.markdown(f"**📝 Резюме:** {st.session_state.ai_summary}")

                if st.session_state.ai_law_refs:
                    st.markdown("**📚 Нормативные документы:**")
                    for ref in st.session_state.ai_law_refs[:5]:
                        if os.path.exists(f"sources/{ref}"):
                            st.markdown(f"- 📄 `{ref}`")
                        else:
                            st.markdown(f"- 📄 {ref}")

                st.markdown("**💡 Рекомендации по всем 9 параметрам:**")

                suggestions = st.session_state.ai_suggestions

                # Отображаем ВСЕ 9 параметров в две колонки
                col_rec1, col_rec2 = st.columns(2)

                with col_rec1:
                    # Категория доступа
                    if "access_category" in suggestions:
                        acc = suggestions["access_category"]
                        eng_value = acc.get('value', 'public')
                        rus_value = RUSSIAN_ACCESS.get(eng_value, eng_value)
                        st.info(f"**Доступ:** {rus_value}  \n*{acc.get('reason', '')}*")

                    # Тип ресурса
                    if "resource_type" in suggestions:
                        rt = suggestions["resource_type"]
                        eng_value = rt.get('value', 'unknown')
                        rus_value = RUSSIAN_TYPE.get(eng_value, eng_value)
                        st.info(f"**Тип:** {rus_value}  \n*{rt.get('reason', '')}*")

                    # Жизненный цикл
                    if "lifecycle" in suggestions:
                        lc = suggestions["lifecycle"]
                        eng_value = lc.get('value', 'unknown')
                        rus_value = RUSSIAN_LIFE.get(eng_value, eng_value)
                        st.info(f"**Жизненный цикл:** {rus_value}  \n*{lc.get('reason', '')}*")

                    # Формат данных
                    if "data_format" in suggestions:
                        df = suggestions["data_format"]
                        eng_value = df.get('value', 'unknown')
                        rus_value = RUSSIAN_FORMAT.get(eng_value, eng_value)
                        st.info(f"**Формат:** {rus_value}  \n*{df.get('reason', '')}*")
                        # Масштаб использования
                    if "usage_scale" in suggestions:
                            us = suggestions["usage_scale"]
                            eng_value = us.get('value', 'unknown')
                            rus_value = RUSSIAN_SCALE.get(eng_value, eng_value)
                            st.info(f"**Масштаб:** {rus_value}  \n*{us.get('reason', '')}*")

                with col_rec2:


                    # Конфиденциальность
                    if "confidentiality" in suggestions:
                        conf = suggestions["confidentiality"]
                        eng_value = conf.get('value', 'unknown')
                        rus_value = RUSSIAN_CONFIDENTIALITY.get(eng_value, eng_value)
                        st.info(f"**Конфиденциальность:** {rus_value}  \n*{conf.get('reason', '')}*")

                    # Количество пользователей
                    if "users_count" in suggestions:
                        users = suggestions["users_count"]
                        eng_value = users.get('value', 'unknown')
                        rus_value = RUSSIAN_USERS.get(eng_value, eng_value)
                        st.info(f"**Пользователей:** {rus_value}  \n*{users.get('reason', '')}*")

                    # Критичность для бизнеса
                    if "business_criticality" in suggestions:
                        crit = suggestions["business_criticality"]
                        eng_value = crit.get('value', 'unknown')
                        rus_value = RUSSIAN_CRITICALITY.get(eng_value, eng_value)
                        st.info(f"**Критичность:** {rus_value}  \n*{crit.get('reason', '')}*")

                    # Резервное копирование
                    if "backup" in suggestions:
                        backup = suggestions["backup"]
                        eng_value = backup.get('value', 'unknown')
                        rus_value = RUSSIAN_BACKUP.get(eng_value, eng_value)
                        st.info(f"**Бэкап:** {rus_value}  \n*{backup.get('reason', '')}*")

    with col2:
        st.subheader("⚙️ Параметры классификации")

        # Получаем рекомендованные значения из ИИ
        suggested_access = None
        suggested_type = None
        suggested_life = None
        suggested_format = None
        suggested_scale = None
        suggested_conf = None
        suggested_users = None
        suggested_crit = None
        suggested_backup = None

        # Получаем рекомендованные значения из ИИ (замените этот блок)
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

        # Основные параметры
        st.markdown("**Основные параметры:**")

        col_a1, col_a2 = st.columns(2)

        with col_a1:
            # Категория доступа
            access_options = list(RUSSIAN_ACCESS.keys())
            default_idx = 0
            if suggested_access and suggested_access in access_options:
                default_idx = access_options.index(suggested_access)

            sel_access = st.selectbox(
                "Категория доступа *",
                options=access_options,
                format_func=lambda x: RUSSIAN_ACCESS[x],
                index=default_idx,
                key="expert_access"
            )

            # Тип ресурса
            type_options = list(RUSSIAN_TYPE.keys())
            default_idx = 0
            if suggested_type and suggested_type in type_options:
                default_idx = type_options.index(suggested_type)

            sel_type = st.selectbox(
                "Тип ресурса *",
                options=type_options,
                format_func=lambda x: RUSSIAN_TYPE[x],
                index=default_idx,
                key="expert_type"
            )

            # Жизненный цикл
            life_options = list(RUSSIAN_LIFE.keys())
            default_idx = 0
            if suggested_life and suggested_life in life_options:
                default_idx = life_options.index(suggested_life)

            sel_life = st.selectbox(
                "Жизненный цикл *",
                options=life_options,
                format_func=lambda x: RUSSIAN_LIFE[x],
                index=default_idx,
                key="expert_life"
            )

        with col_a2:
            # Формат данных
            format_options = list(RUSSIAN_FORMAT.keys())
            default_idx = 0
            if suggested_format and suggested_format in format_options:
                default_idx = format_options.index(suggested_format)

            sel_format = st.selectbox(
                "Формат данных *",
                options=format_options,
                format_func=lambda x: RUSSIAN_FORMAT[x],
                index=default_idx,
                key="expert_format"
            )

            # Масштаб использования
            scale_options = list(RUSSIAN_SCALE.keys())
            default_idx = 0
            if suggested_scale and suggested_scale in scale_options:
                default_idx = scale_options.index(suggested_scale)

            sel_scale = st.selectbox(
                "Масштаб использования *",
                options=scale_options,
                format_func=lambda x: RUSSIAN_SCALE[x],
                index=default_idx,
                key="expert_scale"
            )

        # НОВЫЕ ПАРАМЕТРЫ
        st.markdown("---")
        st.markdown("**🔍 Дополнительные параметры (можно оставить 'Неизвестно'):**")

        col_new1, col_new2 = st.columns(2)

        with col_new1:
            # Уровень конфиденциальности
            conf_options = list(RUSSIAN_CONFIDENTIALITY.keys())
            default_conf_idx = 0
            if suggested_conf and suggested_conf in conf_options:
                default_conf_idx = conf_options.index(suggested_conf)

            sel_conf = st.selectbox(
                "Уровень конфиденциальности",
                options=conf_options,
                format_func=lambda x: RUSSIAN_CONFIDENTIALITY[x],
                index=default_conf_idx,
                key="expert_conf",
                help="Дополнительный уровень секретности (если применимо)"
            )

            # Количество пользователей
            users_options = list(RUSSIAN_USERS.keys())
            default_users_idx = 0
            if suggested_users and suggested_users in users_options:
                default_users_idx = users_options.index(suggested_users)

            sel_users = st.selectbox(
                "Количество пользователей",
                options=users_options,
                format_func=lambda x: RUSSIAN_USERS[x],
                index=default_users_idx,
                key="expert_users",
                help="Сколько человек имеют доступ к ресурсу"
            )

        with col_new2:
            # Критичность для бизнеса
            crit_options = list(RUSSIAN_CRITICALITY.keys())
            default_crit_idx = 0
            if suggested_crit and suggested_crit in crit_options:
                default_crit_idx = crit_options.index(suggested_crit)

            sel_crit = st.selectbox(
                "Критичность для бизнеса",
                options=crit_options,
                format_func=lambda x: RUSSIAN_CRITICALITY[x],
                index=default_crit_idx,
                key="expert_crit",
                help="Насколько критичен ресурс для деятельности"
            )

            # Резервное копирование
            backup_options = list(RUSSIAN_BACKUP.keys())
            default_backup_idx = 0
            if suggested_backup and suggested_backup in backup_options:
                default_backup_idx = backup_options.index(suggested_backup)

            sel_backup = st.selectbox(
                "Резервное копирование",
                options=backup_options,
                format_func=lambda x: RUSSIAN_BACKUP[x],
                index=default_backup_idx,
                key="expert_backup",
                help="Как часто создаются резервные копии"
            )

        # Кнопка сохранения
        st.markdown("---")
        col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
        with col_save2:
            save_resource_btn = st.button(
                "💾 Сохранить ресурс",
                type="primary",
                use_container_width=True,
                disabled=not resource_name
            )

        if save_resource_btn and resource_name:
            # Сохраняем с новыми параметрами
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

            st.success(f"✅ Ресурс '{resource_name}' успешно сохранен! ID: {res_id}")
            st.balloons()

# ВКЛАДКА 2: АНАЛИЗ РАНГА СОХРАНЕННОГО РЕСУРСА
with tab2:
    st.header("📊 Анализ ранга сохраненного ресурса")

    resources = db.get_all_resources_full()

    if not resources:
        st.info("ℹ️ База данных пуста. Сначала добавьте ресурс на первой вкладке.")
    else:
        # Выбор ресурса
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
            load_btn = st.button(
                "📥 Загрузить ресурс",
                type="primary",
                use_container_width=True
            )

        if load_btn and selected_res_id:
            st.session_state.selected_resource_for_analysis = selected_res_id
            st.session_state.calculation_explanation = None
            st.session_state.current_calculation = None
            st.session_state.calculation_result = None  # ← добавить эту строку
            st.rerun()

        # Если ресурс выбран, показываем его параметры
        if st.session_state.selected_resource_for_analysis:
            resource_data = db.get_resource_full_by_id(st.session_state.selected_resource_for_analysis)

            if resource_data:
                # Распаковываем с учетом новых полей
                if len(resource_data) >= 13:  # с новыми полями
                    (res_id, res_name, res_desc, res_category, res_type, res_life,
                     res_format, res_scale, res_conf, res_users, res_crit, res_backup, created_at) = resource_data
                else:  # старый формат
                    res_id, res_name, res_desc, res_category, res_type, res_life, res_format, res_scale, created_at = resource_data
                    res_conf = res_users = res_crit = res_backup = "❓ Неизвестно"

                st.markdown("---")
                st.subheader(f"📋 Параметры ресурса: {res_name}")

                # Отображаем все параметры
                col_params1, col_params2, col_params3 = st.columns(3)
                with col_params1:
                    st.info(f"**📋 Категория доступа:** {res_category}")
                    st.info(f"**📄 Тип ресурса:** {res_type}")
                    st.info(f"**⏱️ Жизненный цикл:** {res_life}")
                with col_params2:
                    st.info(f"**💾 Формат данных:** {res_format}")
                    st.info(f"**📊 Масштаб:** {res_scale}")
                    st.info(f"**🔒 Конфиденциальность:** {res_conf}")
                with col_params3:
                    st.info(f"**👥 Пользователей:** {res_users}")
                    st.info(f"**🎯 Критичность:** {res_crit}")
                    st.info(f"**💾 Бэкап:** {res_backup}")

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

                # История оценок
                history = db.get_evaluation_history(res_id)

                # ========== БЛОК ЭКСПЕРТНОЙ ОЦЕНКИ ==========
                st.markdown("---")
                st.subheader("⚙️ Экспертная оценка (выставьте ранги вручную)")

                # Значения по умолчанию = 1 (при загрузке ресурса)
                default_fin = 1
                default_oper = 1
                default_jur = 1
                default_rep = 1
                default_strat = 1

                # Если есть история, берем последние значения
                if history:
                    last_eval = history[-1]
                    default_fin = last_eval[3]  # rank_fin
                    default_oper = last_eval[4]  # rank_oper
                    default_jur = last_eval[5]  # rank_jur
                    default_rep = last_eval[6]  # rank_rep
                    default_strat = last_eval[7]  # rank_strat

                # Ползунки для эксперта
                # Ползунки для эксперта с динамическими ключами
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

                # Кнопки: слева - сохранить, справа - рассчитать
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])

                with col_btn1:
                    save_direct_btn = st.button(
                        "💾 Сохранить текущую оценку",
                        type="secondary",
                        use_container_width=True,
                        help="Сохранить оценку без расчета (ранги останутся как на ползунках)"
                    )

                with col_btn2:
                    calculate_expert_btn = st.button(
                        "🧮 Рассчитать итоговый ранг",
                        type="primary",
                        use_container_width=True
                    )

                # Прямое сохранение (без расчета)
                if save_direct_btn:
                    expert_ranks = {
                        'fin': expert_fin,
                        'oper': expert_oper,
                        'jur': expert_jur,
                        'rep': expert_rep,
                        'strat': expert_strat
                    }

                    # Нормализация
                    s_scores, total_s = logic.calculate_normalization(expert_ranks)
                    final_rank = logic.get_final_rank(total_s)
                    protection_level = logic.get_protection_level(final_rank)

                    # Подготовка деталей
                    coeff_ranks = logic.calculate_base_ranks(
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

                    details = {
                        'base_ranks': logic.BASE_RANKS_BY_CATEGORY.get(category_key, {}),
                        'coefficients': {
                            'type': coeff_ranks.get('coeff_type', 1.0),
                            'lifecycle': coeff_ranks.get('coeff_life', 1.0),
                            'format': coeff_ranks.get('coeff_format', 1.0),
                            'scale': coeff_ranks.get('coeff_scale', 1.0),
                            'conf': coeff_ranks.get('coeff_conf', 1.0),
                            'users': coeff_ranks.get('coeff_users', 1.0),
                            'business': coeff_ranks.get('coeff_business', 1.0),
                            'backup': coeff_ranks.get('coeff_backup', 1.0)
                        },
                        'formulas': {
                            'fin': coeff_ranks.get('fin_formula', '?'),
                            'oper': coeff_ranks.get('oper_formula', '?'),
                            'jur': coeff_ranks.get('jur_formula', '?'),
                            'rep': coeff_ranks.get('rep_formula', '?'),
                            'strat': coeff_ranks.get('strat_formula', '?')
                        },
                        'params': {
                            'category': category_key,
                            'type': type_key,
                            'lifecycle': life_key,
                            'format': format_key,
                            'scale': scale_key,
                            'conf': conf_key,
                            'users': users_key,
                            'crit': crit_key,
                            'backup': backup_key
                        }
                    }

                    # Сохраняем
                    db.save_evaluation(
                        resource_id=res_id,
                        ranks=expert_ranks,
                        norm_score=total_s,
                        final_rank=final_rank,
                        trigger="Экспертная оценка (прямое сохранение)",
                        details=details
                    )

                    st.success(f"✅ Оценка сохранена! Итоговый ранг: {final_rank}")
                    st.balloons()
                    st.rerun()

                if calculate_expert_btn:
                    # Формируем словарь с рангами эксперта
                    expert_ranks = {
                        'fin': expert_fin,
                        'oper': expert_oper,
                        'jur': expert_jur,
                        'rep': expert_rep,
                        'strat': expert_strat
                    }

                    # Получаем коэффициенты из logic
                    coeff_ranks = logic.calculate_base_ranks(
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

                    # Извлекаем коэффициенты
                    coefficients = {
                        'type': coeff_ranks.get('coeff_type', 1.0),
                        'lifecycle': coeff_ranks.get('coeff_life', 1.0),
                        'format': coeff_ranks.get('coeff_format', 1.0),
                        'scale': coeff_ranks.get('coeff_scale', 1.0),
                        'conf': coeff_ranks.get('coeff_conf', 1.0),
                        'users': coeff_ranks.get('coeff_users', 1.0),
                        'business': coeff_ranks.get('coeff_business', 1.0),
                        'backup': coeff_ranks.get('coeff_backup', 1.0)
                    }

                    # Формируем формулы для отображения
                    formulas = {
                        'fin': coeff_ranks.get('fin_formula', '?'),
                        'oper': coeff_ranks.get('oper_formula', '?'),
                        'jur': coeff_ranks.get('jur_formula', '?'),
                        'rep': coeff_ranks.get('rep_formula', '?'),
                        'strat': coeff_ranks.get('strat_formula', '?')
                    }

                    # Нормализация
                    s_scores, total_s = logic.calculate_normalization(expert_ranks)
                    final_rank = logic.get_final_rank(total_s)
                    protection_level = logic.get_protection_level(final_rank)

                    # Сохраняем результат в сессию
                    st.session_state.calculation_result = {
                        'expert_ranks': expert_ranks,  # ← это значения с ползунков
                        'coefficients': coefficients,
                        'formulas': formulas,
                        'total_s': total_s,
                        'final_rank': final_rank,
                        'protection_level': protection_level
                    }

                    # Запрашиваем объяснение у ИИ
                    # Запрашиваем объяснение у ИИ
                    with st.spinner("🤖 ИИ формирует экспертное заключение..."):
                        params = {
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

                        # ИСПРАВЛЕНО: передаем итоговые ранги из coeff_ranks
                        final_ranks_for_ai = {
                            'fin': coeff_ranks['fin'],
                            'oper': coeff_ranks['oper'],
                            'jur': coeff_ranks['jur'],
                            'rep': coeff_ranks['rep'],
                            'strat': coeff_ranks['strat']
                        }

                        explanation = ai.explain_calculation(
                            res_name,
                            res_desc,
                            params,
                            base_ranks,
                            coefficients,
                            final_ranks_for_ai  # ← теперь здесь итоговые ранги после умножения на коэффициенты!
                        )

                        if "error" not in explanation:
                            st.session_state.calculation_explanation = explanation
                        else:
                            st.warning(f"ИИ не смог сформировать заключение: {explanation['error']}")



                # Отображение результатов расчета
                if st.session_state.get("calculation_result"):
                    result = st.session_state.calculation_result

                    st.markdown("---")
                    st.subheader("📊 Результаты расчета")

                    # Метрики
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
                        st.metric("Интегральный S∑", f"{result['total_s']:.3f}")
                    with col_i2:
                        st.metric("Итоговый ранг", f"{result['final_rank']}")
                    with col_i3:
                        st.metric("Уровень защиты", result['protection_level'])

                    # Детализация расчета
                    with st.expander("🧮 Детализация расчета", expanded=True):
                        st.markdown("### Коэффициенты влияния")
                        coeff_data = {
                            "Параметр": ["Тип ресурса", "Жизненный цикл", "Формат данных", "Масштаб",
                                         "Конфиденциальность", "Пользователи", "Критичность", "Резервное копирование"],
                            "Коэффициент": [
                                f"{result['coefficients']['type']:.2f}",
                                f"{result['coefficients']['lifecycle']:.2f}",
                                f"{result['coefficients']['format']:.2f}",
                                f"{result['coefficients']['scale']:.2f}",
                                f"{result['coefficients']['conf']:.2f}",
                                f"{result['coefficients']['users']:.2f}",
                                f"{result['coefficients']['business']:.2f}",
                                f"{result['coefficients']['backup']:.2f}"
                            ]
                        }
                        st.table(pd.DataFrame(coeff_data))

                        st.markdown("### Формулы расчета")
                        formula_data = {
                            "Критерий": ["Финансовый", "Операционный", "Юридический", "Репутационный",
                                         "Стратегический"],
                            "Формула": [
                                result['formulas']['fin'],
                                result['formulas']['oper'],
                                result['formulas']['jur'],
                                result['formulas']['rep'],
                                result['formulas']['strat']
                            ]
                        }
                        st.table(pd.DataFrame(formula_data))

                    # Экспертное заключение ИИ
                    if st.session_state.get("calculation_explanation"):
                        with st.expander("📚 Экспертное заключение ИИ (на основе НПА)", expanded=True):
                            exp = st.session_state.calculation_explanation

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
                                        if "law_refs" in exp["explanations"][crit]:
                                            st.caption(
                                                "📄 Источники: " + ", ".join(exp["explanations"][crit]["law_refs"]))
                                        st.markdown("---")

                    # Кнопка сохранения (после расчета)
                    st.markdown("---")

                    need_save = True
                    if history:
                        last_date = datetime.strptime(history[-1][0], "%Y-%m-%d %H:%M:%S")
                        now = datetime.now()
                        if (now - last_date).days < 1 and history[-1][2] == result['final_rank']:
                            need_save = False
                            st.info("ℹ️ Оценка не изменилась с последнего раза. Сохранение не требуется.")

                    if need_save:
                        col_save1, col_save2, col_save3 = st.columns([1, 1, 1])
                        with col_save2:
                            if st.button("💾 Сохранить оценку в историю (после расчета)", use_container_width=True):
                                details = {
                                    'base_ranks': logic.BASE_RANKS_BY_CATEGORY.get(category_key, {}),
                                    'coefficients': result['coefficients'],
                                    'formulas': result['formulas'],
                                    'params': {
                                        'category': category_key,
                                        'type': type_key,
                                        'lifecycle': life_key,
                                        'format': format_key,
                                        'scale': scale_key,
                                        'conf': conf_key,
                                        'users': users_key,
                                        'crit': crit_key,
                                        'backup': backup_key
                                    }
                                }

                                db.save_evaluation(
                                    resource_id=res_id,
                                    ranks=result['expert_ranks'],
                                    norm_score=result['total_s'],
                                    final_rank=result['final_rank'],
                                    trigger="Экспертная оценка (после расчета)",
                                    details=details
                                )

                                st.success(f"✅ Оценка сохранена! Итоговый ранг: {result['final_rank']}")
                                st.balloons()
                                st.rerun()
# ============================================================================
# ВКЛАДКА 3: ДИНАМИКА И ИНЦИДЕНТЫ
# ============================================================================
with tab3:
    st.header("⚡ Анализ динамики ценности при инцидентах")

    resources = db.get_all_resources_full()

    if not resources:
        st.info("ℹ️ База данных пуста. Сначала добавьте ресурс на первой вкладке.")
    else:
        # Селектор ресурса
        res_dict = {r[0]: f"ID {r[0]}: {r[1]} ({r[2]})" for r in resources}

        selected_res_id = st.selectbox(
            "Выберите ресурс для анализа динамики",
            options=list(res_dict.keys()),
            format_func=lambda x: res_dict[x],
            key="incident_res_selector"
        )

        # Получаем историю оценок
        history = db.get_evaluation_history(selected_res_id)

        if not history:
            st.warning("⚠️ Для этого ресурса еще нет оценок. Сначала проведите анализ на вкладке 2.")
        else:
            # График динамики
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

            # Текущие параметры ресурса
            resource_data = db.get_resource_full_by_id(selected_res_id)
            if resource_data:
                if len(resource_data) >= 13:
                    (res_id, res_name, res_desc, res_category, res_type, res_life,
                     res_format, res_scale, res_conf, res_users, res_crit, res_backup, _) = resource_data
                else:
                    res_id, res_name, res_desc, res_category, res_type, res_life, res_format, res_scale, _ = resource_data
                    res_conf = res_users = res_crit = res_backup = "❓ Неизвестно"

                # Блок анализа инцидента
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

                        analysis = ai.analyze_incident(
                            res_name,
                            res_desc,
                            current_params,
                            event_name
                        )

                        if "error" not in analysis:
                            st.session_state.incident_analysis = analysis
                            st.success("✅ Анализ получен")
                        else:
                            st.error(f"Ошибка: {analysis['error']}")

                # Отображение рекомендаций ИИ
                if st.session_state.get("incident_analysis"):
                    analysis = st.session_state.incident_analysis

                    with st.expander("🤖 Рекомендации ИИ по изменению параметров", expanded=True):
                        if "summary" in analysis:
                            st.info(f"**Общий вывод:** {analysis['summary']}")

                        if "analysis" in analysis:
                            for param, data in analysis["analysis"].items():
                                if data.get("should_change"):
                                    st.warning(f"**{param}:** требуется изменение")
                                    st.markdown(f"*Направление:* {data.get('direction', '?')}")
                                    st.markdown(f"*Причина:* {data.get('reason', '?')}")
                                    if "recommendation" in data:
                                        st.markdown(f"*Рекомендация:* {data['recommendation']}")
                                    st.markdown("---")

                # Форма для переоценки
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

                    col_r1, col_r2 = st.columns(2)

                    with col_r1:
                        new_fin = st.slider("💰 Финансовый (1-10)", 1, 10, current_ranks['fin'], key="inc_fin")
                        new_oper = st.slider("⚙️ Операционный (1-10)", 1, 10, current_ranks['oper'], key="inc_oper")
                        new_jur = st.slider("⚖️ Юридический (1-8)", 1, 8, current_ranks['jur'], key="inc_jur")

                    with col_r2:
                        new_rep = st.slider("📢 Репутационный (1-8)", 1, 8, current_ranks['rep'], key="inc_rep")
                        new_strat = st.slider("🚩 Стратегический (1-8)", 1, 8, current_ranks['strat'], key="inc_strat")

                        if st.button("💾 Зафиксировать событие и сохранить", type="primary", use_container_width=True):
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
                                    selected_res_id,
                                    new_ranks,
                                    total_s,
                                    final_rank,
                                    trigger=event_name
                                )

                                st.success(f"✅ Событие зафиксировано! Новый ранг: {final_rank}")
                                st.session_state.incident_analysis = None
                                st.rerun()
                            else:
                                st.error("❌ Введите описание события")

# ============================================================================
# ВКЛАДКА 4: БАЗА РЕСУРСОВ И ОТЧЕТЫ
# ============================================================================
with tab4:
    st.header("📚 База информационных ресурсов и отчеты")

    resources = db.get_all_resources_full()

    if resources:
        # Проверяем, есть ли новые поля
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

        # Статистика
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

        # Распределение по категориям
        cat_stats = db.get_resources_by_category()
        if cat_stats:
            st.subheader("📊 Распределение по категориям")
            df_cat = pd.DataFrame(cat_stats, columns=["Категория", "Количество"])
            st.bar_chart(df_cat.set_index("Категория"))

        # Детальная информация
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

                # Экспорт
                csv = df_detail[display_cols].to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Скачать историю (CSV)",
                    csv,
                    f"resource_{res_for_detail}_history.csv",
                    "text/csv",
                    use_container_width=True
                )

                # Детали последней оценки
                if df_detail.iloc[-1]["Детали"]:
                    with st.expander("📋 Детали последнего расчета"):
                        try:
                            details = json.loads(df_detail.iloc[-1]["Детали"])
                            st.json(details)
                        except:
                            st.write(df_detail.iloc[-1]["Детали"])
            else:
                st.info("ℹ️ Для этого ресурса еще нет оценок.")

        # Кнопка оптимизации
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