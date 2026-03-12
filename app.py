# app.py
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import modules.ai_analyst as ai
import database as db
import logic

st.set_page_config(
    page_title="СППР Оценка динамики ценности ИР",
    page_icon="🛡️",
    layout="wide"
)


# Инициализация состояния сессии
def init_session_state():
    """Инициализация всех переменных состояния сессии"""
    if "ai_suggestions" not in st.session_state:
        st.session_state.ai_suggestions = None
    if "ai_incident_suggestions" not in st.session_state:
        st.session_state.ai_incident_suggestions = None
    if "resource_saved" not in st.session_state:
        st.session_state.resource_saved = False
    if "current_resource_id" not in st.session_state:
        st.session_state.current_resource_id = None
    if "show_rank_analysis" not in st.session_state:
        st.session_state.show_rank_analysis = False
    if "analysis_completed" not in st.session_state:
        st.session_state.analysis_completed = False
    if "analysis_triggered" not in st.session_state:
        st.session_state.analysis_triggered = False
    if "rank_analysis_result" not in st.session_state:
        st.session_state.rank_analysis_result = None
    if "calculated_ranks" not in st.session_state:
        st.session_state.calculated_ranks = None
    # Новые переменные для загрузки ресурса из базы
    if "show_loaded_analysis" not in st.session_state:
        st.session_state.show_loaded_analysis = False
    if "analyze_resource_id" not in st.session_state:
        st.session_state.analyze_resource_id = None
    if "analyze_resource_name" not in st.session_state:
        st.session_state.analyze_resource_name = None
    if "analyze_resource_desc" not in st.session_state:
        st.session_state.analyze_resource_desc = None
    if "analyze_resource_category" not in st.session_state:
        st.session_state.analyze_resource_category = None
    if "analyze_resource_type" not in st.session_state:
        st.session_state.analyze_resource_type = None
    if "analyze_resource_lifecycle" not in st.session_state:
        st.session_state.analyze_resource_lifecycle = None
    if "analyze_resource_format" not in st.session_state:
        st.session_state.analyze_resource_format = None
    if "analyze_resource_scale" not in st.session_state:
        st.session_state.analyze_resource_scale = None
    # Переменная для хранения выбранного ресурса на вкладке 2
    if "selected_resource_for_analysis" not in st.session_state:
        st.session_state.selected_resource_for_analysis = None
    # Переменная для сохранения рассчитанных рангов
    if "calculated_ranks_for_save" not in st.session_state:
        st.session_state.calculated_ranks_for_save = None
    if "current_resource_for_save" not in st.session_state:
        st.session_state.current_resource_for_save = None


init_session_state()

# Словари для перевода на русский
RUSSIAN_ACCESS = {
    "public": "📢 Общедоступная",
    "internal": "🏢 Внутренняя (ДСП)",
    "personal_data": "👤 Персональные данные (ПДн)",
    "trade_secret": "🔒 Коммерческая тайна (КТ)",
    "state_secret": "⚡ Государственная тайна",
    "copyright": "© Интеллектуальная собственность"
}

RUSSIAN_TYPE = {
    "software": "💻 Программное обеспечение",
    "database": "🗄️ База данных",
    "financial": "💰 Финансовая отчетность",
    "document": "📄 Текстовая документация",
    "media": "🎬 Мультимедиа"
}

RUSSIAN_LIFE = {
    "short_term": "⏱️ Краткосрочный (дни/месяцы)",
    "medium_term": "📅 Среднесрочный (до 1 года)",
    "long_term": "📆 Долгосрочный (более 1 года)"
}

RUSSIAN_FORMAT = {
    "structured": "🗂️ Структурированные (БД/JSON)",
    "source_code": "👨‍💻 Исходный код",
    "text": "📝 Текстовые документы",
    "archive": "📦 Архивы",
    "multimedia": "🎥 Мультимедиа"
}

RUSSIAN_SCALE = {
    "local": "👤 Локальный (единицы людей)",
    "department": "👥 Уровень отдела",
    "enterprise": "🏭 Масштаб предприятия"
}

# Обратные словари для преобразования русских названий в ключи
REVERSE_ACCESS = {v: k for k, v in RUSSIAN_ACCESS.items()}
REVERSE_TYPE = {v: k for k, v in RUSSIAN_TYPE.items()}
REVERSE_LIFE = {v: k for k, v in RUSSIAN_LIFE.items()}
REVERSE_FORMAT = {v: k for k, v in RUSSIAN_FORMAT.items()}
REVERSE_SCALE = {v: k for k, v in RUSSIAN_SCALE.items()}

# Заголовок приложения
st.title("🛡️ Система поддержки принятия решений для оценки динамики ценности информационных ресурсов")
st.markdown("---")

# Описание методики (важно для ВКР!)
with st.expander("📚 О методике оценки (НИР Глава 4)", expanded=False):
    st.markdown("""
    ### Математическая модель оценки ценности ИР

    **Формула расчета частного ранга:**
    $R_{критерий} = R_{base} \\times K_{type} \\times K_{life} \\times K_{format} \\times K_{scale}$

    **Группа А (Критические критерии, шкала 1-8):**
    - **Финансовый ущерб (fin)** - прямые и косвенные потери
    - **Операционный сбой (oper)** - влияние на бизнес-процессы

    **Группа Б (Качественные критерии, шкала 1-5):**
    - **Юридический риск (jur)** - ответственность по НПА
    - **Репутационный ущерб (rep)** - имиджевые потери
    - **Стратегический ущерб (strat)** - влияние на развитие

    **Нормализация:** $S_{критерий} = \\frac{R_{факт} - 1}{R_{max} - 1}$

    **Итоговый ранг ценности** определяется по интегральной сумме $S_\\Sigma$
    """)

# Основные вкладки - НОВАЯ СТРУКТУРА
tab1, tab2, tab3, tab4 = st.tabs([
    "📝 1. Регистрация и базовая оценка",
    "📊 2. Анализ ранга сохраненного ресурса",
    "⚡ 3. Динамика и инциденты",
    "📚 4. База ресурсов и отчеты"
])

# ============================================================================
# ВКЛАДКА 1: РЕГИСТРАЦИЯ И БАЗОВАЯ ОЦЕНКА
# ============================================================================
with tab1:
    st.header("Регистрация нового информационного ресурса")

    # Основные колонки для ввода
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📋 Исходные данные")

        # Основная информация
        resource_name = st.text_input(
            "Название ресурса *",
            placeholder="Например: Патент на изобретение",
            key="input_name"
        )

        resource_desc = st.text_area(
            "Описание ресурса",
            placeholder="Опишите назначение, содержание, кто работает с ресурсом, срок хранения, формат данных...",
            height=200,
            key="input_desc"
        )

        # Кнопка запроса к ИИ
        col_ai_btn, col_ai_status = st.columns([1, 2])
        with col_ai_btn:
            ai_request_btn = st.button(
                "🤖 Запросить анализ ИИ",
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
                analysis = ai.get_ai_analysis(resource_name, resource_desc)

                if "error" not in analysis:
                    st.session_state.ai_suggestions = analysis.get("suggestions", {})
                    st.session_state.ai_law_refs = analysis.get("law_refs", [])
                    st.session_state.ai_summary = analysis.get("summary", "")
                    st.session_state.resource_saved = False
                    st.session_state.show_rank_analysis = False
                    st.session_state.analysis_triggered = False
                    st.rerun()
                else:
                    st.error(f"Ошибка при анализе: {analysis['error']}")

        # Отображение рекомендаций ИИ (если есть)
        if st.session_state.ai_suggestions:
            with st.expander("🤖 Рекомендации ИИ-ассистента", expanded=True):
                st.markdown(f"**📝 Резюме:** {st.session_state.ai_summary}")

                # Ссылки на документы
                if st.session_state.ai_law_refs:
                    st.markdown("**📚 Нормативные документы:**")
                    for ref in st.session_state.ai_law_refs:
                        if os.path.exists(f"sources/{ref}"):
                            st.markdown(f"- 📄 `{ref}`")
                        else:
                            st.markdown(f"- 📄 {ref}")

                st.markdown("**💡 Рекомендации по категориям:**")

                # Отображаем рекомендации для каждой категории
                suggestions = st.session_state.ai_suggestions

                # Категория доступа
                if "access_category" in suggestions:
                    acc = suggestions["access_category"]
                    eng_value = acc.get('value', '—')
                    rus_value = RUSSIAN_ACCESS.get(eng_value, eng_value)
                    law_file = acc.get('law_file', '')
                    law_text = f" (`{law_file}`)" if law_file and os.path.exists(f"sources/{law_file}") else ""
                    st.info(f"**Доступ:** {rus_value}{law_text}  \n*{acc.get('reason', '')}*")

                # Тип ресурса
                if "resource_type" in suggestions:
                    rt = suggestions["resource_type"]
                    eng_value = rt.get('value', '—')
                    rus_value = RUSSIAN_TYPE.get(eng_value, eng_value)
                    law_file = rt.get('law_file', '')
                    law_text = f" (`{law_file}`)" if law_file and os.path.exists(f"sources/{law_file}") else ""
                    st.info(f"**Тип:** {rus_value}{law_text}  \n*{rt.get('reason', '')}*")

                # Жизненный цикл
                if "lifecycle" in suggestions:
                    lc = suggestions["lifecycle"]
                    eng_value = lc.get('value', '—')
                    rus_value = RUSSIAN_LIFE.get(eng_value, eng_value)
                    law_file = lc.get('law_file', '')
                    law_text = f" (`{law_file}`)" if law_file and os.path.exists(f"sources/{law_file}") else ""
                    st.info(f"**Жизненный цикл:** {rus_value}{law_text}  \n*{lc.get('reason', '')}*")

                # Формат данных
                if "data_format" in suggestions:
                    df = suggestions["data_format"]
                    eng_value = df.get('value', '—')
                    rus_value = RUSSIAN_FORMAT.get(eng_value, eng_value)
                    law_file = df.get('law_file', '')
                    law_text = f" (`{law_file}`)" if law_file and os.path.exists(f"sources/{law_file}") else ""
                    st.info(f"**Формат:** {rus_value}{law_text}  \n*{df.get('reason', '')}*")

                # Масштаб использования
                if "usage_scale" in suggestions:
                    us = suggestions["usage_scale"]
                    eng_value = us.get('value', '—')
                    rus_value = RUSSIAN_SCALE.get(eng_value, eng_value)
                    law_file = us.get('law_file', '')
                    law_text = f" (`{law_file}`)" if law_file and os.path.exists(f"sources/{law_file}") else ""
                    st.info(f"**Масштаб:** {rus_value}{law_text}  \n*{us.get('reason', '')}*")

    with col2:
        st.subheader("⚙️ Параметры классификации (решение эксперта)")

        # Получаем значения из session_state или устанавливаем по умолчанию
        if "sel_access" not in st.session_state:
            st.session_state.sel_access = list(RUSSIAN_ACCESS.keys()).index("public")
        if "sel_type" not in st.session_state:
            st.session_state.sel_type = list(RUSSIAN_TYPE.keys()).index("document")
        if "sel_life" not in st.session_state:
            st.session_state.sel_life = list(RUSSIAN_LIFE.keys()).index("medium_term")
        if "sel_format" not in st.session_state:
            st.session_state.sel_format = list(RUSSIAN_FORMAT.keys()).index("text")
        if "sel_scale" not in st.session_state:
            st.session_state.sel_scale = list(RUSSIAN_SCALE.keys()).index("department")

        # Элементы ввода для эксперта с использованием session_state
        sel_access = st.selectbox(
            "Категория доступа",
            options=list(RUSSIAN_ACCESS.keys()),
            format_func=lambda x: RUSSIAN_ACCESS[x],
            index=st.session_state.sel_access,
            key="expert_access",
            help="Определяет базовый уровень риска согласно законодательству РФ"
        )
        st.session_state.sel_access = list(RUSSIAN_ACCESS.keys()).index(sel_access)

        sel_type = st.selectbox(
            "Тип ресурса",
            options=list(RUSSIAN_TYPE.keys()),
            format_func=lambda x: RUSSIAN_TYPE[x],
            index=st.session_state.sel_type,
            key="expert_type",
            help="Влияет на сложность восстановления и критичность"
        )
        st.session_state.sel_type = list(RUSSIAN_TYPE.keys()).index(sel_type)

        sel_life = st.selectbox(
            "Жизненный цикл",
            options=list(RUSSIAN_LIFE.keys()),
            format_func=lambda x: RUSSIAN_LIFE[x],
            index=st.session_state.sel_life,
            key="expert_life",
            help="Определяет период актуальности информации"
        )
        st.session_state.sel_life = list(RUSSIAN_LIFE.keys()).index(sel_life)

        sel_format = st.selectbox(
            "Формат данных",
            options=list(RUSSIAN_FORMAT.keys()),
            format_func=lambda x: RUSSIAN_FORMAT[x],
            index=st.session_state.sel_format,
            key="expert_format",
            help="Влияет на возможности утечки и восстановления"
        )
        st.session_state.sel_format = list(RUSSIAN_FORMAT.keys()).index(sel_format)

        sel_scale = st.selectbox(
            "Масштаб использования",
            options=list(RUSSIAN_SCALE.keys()),
            format_func=lambda x: RUSSIAN_SCALE[x],
            index=st.session_state.sel_scale,
            key="expert_scale",
            help="Определяет широту воздействия при инцидентах"
        )
        st.session_state.sel_scale = list(RUSSIAN_SCALE.keys()).index(sel_scale)

        # Кнопка сохранения ресурса
        col_save1, col_save2 = st.columns(2)
        with col_save1:
            save_resource_btn = st.button(
                "💾 Сохранить ресурс",
                type="primary",
                use_container_width=True,
                disabled=not resource_name
            )
        with col_save2:
            if st.session_state.resource_saved:
                st.success("✅ Ресурс сохранен")

        # Обработка сохранения ресурса
        if save_resource_btn and resource_name:
            # Сохраняем ресурс в БД со всеми параметрами
            res_id = db.add_resource(
                resource_name,
                resource_desc,
                RUSSIAN_ACCESS[sel_access],
                RUSSIAN_TYPE[sel_type],
                RUSSIAN_LIFE[sel_life],
                RUSSIAN_FORMAT[sel_format],
                RUSSIAN_SCALE[sel_scale]
            )

            st.session_state.current_resource_id = res_id
            st.session_state.resource_saved = True
            st.session_state.show_rank_analysis = True
            st.session_state.analysis_completed = False
            st.session_state.analysis_triggered = False
            # Сохраняем параметры в session_state для последующего использования
            st.session_state.saved_sel_access = sel_access
            st.session_state.saved_sel_type = sel_type
            st.session_state.saved_sel_life = sel_life
            st.session_state.saved_sel_format = sel_format
            st.session_state.saved_sel_scale = sel_scale

            st.success(f"✅ Ресурс '{resource_name}' успешно сохранен! ID: {res_id}")
            st.rerun()

# ============================================================================
# ВКЛАДКА 2: АНАЛИЗ РАНГА СОХРАНЕННОГО РЕСУРСА
# ============================================================================
with tab2:
    st.header("📊 Анализ ранга сохраненного ресурса")

    # Получаем список всех ресурсов
    resources = db.get_all_resources_full()

    if not resources:
        st.info("ℹ️ База данных пуста. Сначала добавьте ресурс на первой вкладке.")
    else:
        # Создаем DataFrame для отображения
        df_resources = pd.DataFrame(resources, columns=["ID", "Название", "Категория", "Описание", "Дата"])

        # Выбор ресурса
        col_select, col_btn = st.columns([3, 1])

        with col_select:
            resource_options = {r[0]: f"{r[0]}: {r[1]} ({r[2]})" for r in resources}
            selected_res_id = st.selectbox(
                "Выберите ресурс для анализа",
                options=list(resource_options.keys()),
                format_func=lambda x: resource_options[x],
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
            st.rerun()

        # Если ресурс выбран, показываем его параметры
        if st.session_state.selected_resource_for_analysis:
            # Получаем полные данные ресурса
            resource_data = db.get_resource_full_by_id(st.session_state.selected_resource_for_analysis)

            if resource_data:
                res_id, res_name, res_desc, res_category, res_type, res_life, res_format, res_scale, created_at = resource_data

                st.markdown("---")
                st.subheader(f"📋 Параметры ресурса: {res_name}")

                # Отображаем параметры в две колонки
                col_params1, col_params2 = st.columns(2)

                with col_params1:
                    st.info(f"**📋 Категория доступа:** {res_category}")
                    st.info(f"**📄 Тип ресурса:** {res_type}")
                    st.info(f"**⏱️ Жизненный цикл:** {res_life}")

                with col_params2:
                    st.info(f"**💾 Формат данных:** {res_format}")
                    st.info(f"**📊 Масштаб:** {res_scale}")

                with st.expander("📝 Полное описание"):
                    st.write(res_desc)

                # Проверяем, есть ли уже оценки для этого ресурса
                history = db.get_evaluation_history(res_id)

                if history:
                    st.markdown("---")
                    st.subheader("📊 Существующие оценки")

                    # Показываем историю оценок
                    df_history = pd.DataFrame(
                        history,
                        columns=["Дата", "Событие", "Итоговый ранг", "Фин", "Опер", "Юр", "Реп", "Страт", "S∑"]
                    )
                    st.dataframe(df_history, use_container_width=True)

                    # Показываем последнюю оценку (текущую)
                    last_eval = history[-1]
                    st.markdown("### Текущие ранги (последняя оценка)")

                    col_curr1, col_curr2 = st.columns(2)
                    with col_curr1:
                        st.metric("💰 Финансовый", last_eval[3])
                        st.metric("⚙️ Операционный", last_eval[4])
                        st.metric("⚖️ Юридический", last_eval[5])
                    with col_curr2:
                        st.metric("📢 Репутационный", last_eval[6])
                        st.metric("🚩 Стратегический", last_eval[7])
                        st.metric("📊 Итоговый ранг", last_eval[2])

                    st.warning(
                        "⚠️ Для этого ресурса уже есть оценки. Для изменения рангов перейдите на вкладку 'Динамика и инциденты'.")

                else:
                    st.markdown("---")
                    st.subheader("🧮 Провести первичный анализ ранга")
                    st.info(
                        "ℹ️ Для этого ресурса еще нет оценок. Нажмите кнопку ниже для анализа с обоснованием от ИИ.")

                    # Кнопка для анализа с ИИ
                    col_analyze1, col_analyze2, col_analyze3 = st.columns([1, 1, 1])
                    with col_analyze2:
                        analyze_ai_btn = st.button(
                            "🤖 Анализ с ИИ",
                            type="primary",
                            use_container_width=True
                        )

                    # Преобразуем русские названия обратно в ключи для передачи в ИИ
                    category_key = REVERSE_ACCESS.get(res_category, "public")
                    type_key = REVERSE_TYPE.get(res_type, "document")
                    life_key = REVERSE_LIFE.get(res_life, "medium_term")
                    format_key = REVERSE_FORMAT.get(res_format, "text")
                    scale_key = REVERSE_SCALE.get(res_scale, "department")

                    # Рассчитываем базовые ранги для ползунков
                    base_ranks = logic.calculate_base_ranks(
                        category_key, type_key, life_key, format_key, scale_key
                    )

                    if analyze_ai_btn:
                        with st.spinner(
                                "🧠 ИИ анализирует ресурс и формирует обоснование... Это может занять некоторое время."):

                            # Получаем анализ от ИИ
                            rank_analysis = ai.get_rank_analysis(
                                res_name,
                                res_desc,
                                category_key,
                                type_key,
                                life_key,
                                format_key,
                                scale_key
                            )

                            if "error" not in rank_analysis:
                                st.session_state.rank_analysis_result = rank_analysis
                                st.success("✅ Анализ получен!")
                            else:
                                st.error(f"Ошибка при анализе: {rank_analysis['error']}")

                    # Если есть результаты анализа, показываем их
                    if st.session_state.get("rank_analysis_result"):
                        result = st.session_state.rank_analysis_result

                        # Показываем общее заключение
                        if "summary" in result:
                            st.info(f"**📋 Заключение ИИ:** {result['summary']}")

                        # Показываем нормативные документы
                        if "law_refs" in result and result["law_refs"]:
                            with st.expander("📚 Нормативные документы, использованные при анализе"):
                                for ref in result["law_refs"]:
                                    if os.path.exists(f"sources/{ref}"):
                                        st.markdown(f"- 📄 `{ref}`")
                                    else:
                                        st.markdown(f"- 📄 {ref}")

                        # Получаем ранги из результата или используем расчетные
                        if "rank_analysis" in result:
                            rank_data = result["rank_analysis"]

                            # Извлекаем значения с приоритетом от ИИ
                            fin_val = rank_data.get('fin', {}).get('value', base_ranks['fin'])
                            oper_val = rank_data.get('oper', {}).get('value', base_ranks['oper'])
                            jur_val = rank_data.get('jur', {}).get('value', base_ranks['jur'])
                            rep_val = rank_data.get('rep', {}).get('value', base_ranks['rep'])
                            strat_val = rank_data.get('strat', {}).get('value', base_ranks['strat'])

                            fin_reason = rank_data.get('fin', {}).get('reasoning', '')
                            oper_reason = rank_data.get('oper', {}).get('reasoning', '')
                            jur_reason = rank_data.get('jur', {}).get('reasoning', '')
                            rep_reason = rank_data.get('rep', {}).get('reasoning', '')
                            strat_reason = rank_data.get('strat', {}).get('reasoning', '')

                            fin_law = rank_data.get('fin', {}).get('law_ref', '')
                            oper_law = rank_data.get('oper', {}).get('law_ref', '')
                            jur_law = rank_data.get('jur', {}).get('law_ref', '')
                            rep_law = rank_data.get('rep', {}).get('law_ref', '')
                            strat_law = rank_data.get('strat', {}).get('law_ref', '')
                        else:
                            # Если нет анализа, используем расчетные
                            fin_val = oper_val = jur_val = rep_val = strat_val = 1
                            fin_reason = oper_reason = jur_reason = rep_reason = strat_reason = "Анализ не выполнен"
                            fin_law = oper_law = jur_law = rep_law = strat_law = ""

                        st.markdown("### Результаты расчета с обоснованием")

                        # Ползунки с обоснованием
                        col_r1, col_r2 = st.columns(2)

                        with col_r1:
                            st.markdown("**💰 Финансовый ущерб (1-8)**")
                            r_fin = st.slider(
                                "Финансовый",
                                min_value=1, max_value=8,
                                value=int(fin_val),
                                key="rank_fin_slider",
                                label_visibility="collapsed"
                            )
                            if fin_reason:
                                if fin_law:
                                    st.info(f"📌 {fin_reason}\n\n*Источник: {fin_law}*")
                                else:
                                    st.info(f"📌 {fin_reason}")

                            st.markdown("**⚙️ Операционный сбой (1-8)**")
                            r_oper = st.slider(
                                "Операционный",
                                min_value=1, max_value=8,
                                value=int(oper_val),
                                key="rank_oper_slider",
                                label_visibility="collapsed"
                            )
                            if oper_reason:
                                if oper_law:
                                    st.info(f"📌 {oper_reason}\n\n*Источник: {oper_law}*")
                                else:
                                    st.info(f"📌 {oper_reason}")

                        with col_r2:
                            st.markdown("**⚖️ Юридический риск (1-5)**")
                            r_jur = st.slider(
                                "Юридический",
                                min_value=1, max_value=5,
                                value=int(jur_val),
                                key="rank_jur_slider",
                                label_visibility="collapsed"
                            )
                            if jur_reason:
                                if jur_law:
                                    st.info(f"📌 {jur_reason}\n\n*Источник: {jur_law}*")
                                else:
                                    st.info(f"📌 {jur_reason}")

                            st.markdown("**📢 Репутационный ущерб (1-5)**")
                            r_rep = st.slider(
                                "Репутационный",
                                min_value=1, max_value=5,
                                value=int(rep_val),
                                key="rank_rep_slider",
                                label_visibility="collapsed"
                            )
                            if rep_reason:
                                if rep_law:
                                    st.info(f"📌 {rep_reason}\n\n*Источник: {rep_law}*")
                                else:
                                    st.info(f"📌 {rep_reason}")

                            st.markdown("**🚩 Стратегический ущерб (1-5)**")
                            r_strat = st.slider(
                                "Стратегический",
                                min_value=1, max_value=5,
                                value=int(strat_val),
                                key="rank_strat_slider",
                                label_visibility="collapsed"
                            )
                            if strat_reason:
                                if strat_law:
                                    st.info(f"📌 {strat_reason}\n\n*Источник: {strat_law}*")
                                else:
                                    st.info(f"📌 {strat_reason}")

                        # Кнопка сохранения
                        if st.button("💾 Сохранить оценку в историю", use_container_width=True):
                            final_ranks = {
                                'fin': r_fin, 'oper': r_oper,
                                'jur': r_jur, 'rep': r_rep, 'strat': r_strat
                            }

                            # Нормализация
                            s_scores, total_s = logic.calculate_normalization(final_ranks)
                            final_rank = logic.get_final_rank(total_s)

                            # Сохраняем
                            db.save_evaluation(
                                res_id,
                                final_ranks,
                                total_s,
                                final_rank,
                                trigger="Первичная оценка (с обоснованием ИИ)"
                            )

                            st.success(f"✅ Оценка сохранена! Итоговый ранг: {final_rank}")
                            st.balloons()

                            # Показываем итоговые метрики
                            col_m1, col_m2, col_m3 = st.columns(3)
                            with col_m1:
                                st.metric("Интегральная сумма S∑", f"{total_s:.3f}")
                            with col_m2:
                                st.metric("Итоговый ранг", final_rank)
                            with col_m3:
                                protection_level = {
                                    1: "Базовый (открытая инф.)",
                                    2: "Базовый",
                                    3: "Стандартный",
                                    4: "Стандартный",
                                    5: "Повышенный",
                                    6: "Повышенный",
                                    7: "Высокий",
                                    8: "Высокий",
                                    9: "Максимальный"
                                }.get(final_rank, "Не определен")
                                st.metric("Уровень защиты", protection_level)

# ============================================================================
# ВКЛАДКА 3: ДИНАМИКА И ИНЦИДЕНТЫ
# ============================================================================
with tab3:
    st.header("⚡ Анализ динамики ценности при инцидентах")

    # Получаем список ресурсов
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
            st.warning("⚠️ Для этого ресурса еще нет оценок. Сначала проведите первичный анализ на вкладке 2.")
        else:
            # График динамики
            st.subheader("📈 Динамика изменения ценности")

            df_history = pd.DataFrame(
                history,
                columns=["Дата", "Событие", "Ранг", "Фин", "Опер", "Юр", "Реп", "Страт", "S∑"]
            )

            # График
            chart_data = df_history[["Дата", "Ранг"]].set_index("Дата")
            st.line_chart(chart_data)

            # Таблица истории
            with st.expander("📋 История оценок", expanded=False):
                st.dataframe(df_history, use_container_width=True)

            st.markdown("---")

            # Текущие ранги
            last_eval = history[-1]
            current_ranks = {
                'fin': last_eval[3], 'oper': last_eval[4],
                'jur': last_eval[5], 'rep': last_eval[6], 'strat': last_eval[7]
            }

            # Блок анализа инцидента
            st.subheader("⚡ Фиксация инициирующего события")

            col_event1, col_event2 = st.columns([2, 1])

            with col_event1:
                event_name = st.text_input(
                    "Описание события",
                    placeholder="Например: Обнаружена критическая уязвимость, утечка данных, установка патча...",
                    key="incident_event"
                )

            with col_event2:
                analyze_incident_btn = st.button(
                    "🤖 Анализ инцидента",
                    type="secondary",
                    use_container_width=True,
                    disabled=not event_name
                )

            # Анализ инцидента ИИ
            if analyze_incident_btn and event_name:
                with st.spinner("🔍 ИИ анализирует последствия инцидента..."):
                    analysis = ai.get_ai_incident_analysis(
                        res_dict[selected_res_id],
                        event_name,
                        current_ranks
                    )

                    if "error" not in analysis:
                        st.session_state.ai_incident_suggestions = analysis
                        st.success("✅ Анализ инцидента получен")
                    else:
                        st.error(f"Ошибка: {analysis['error']}")

            # Отображение рекомендаций ИИ по инциденту
            if st.session_state.ai_incident_suggestions:
                suggestions = st.session_state.ai_incident_suggestions

                with st.expander("🤖 Рекомендации ИИ по инциденту", expanded=True):
                    if "reasoning" in suggestions:
                        st.info(f"**Анализ:** {suggestions['reasoning']}")

                    if "law_refs" in suggestions and suggestions["law_refs"]:
                        st.markdown("**📚 Нормативные документы:**")
                        for ref in suggestions["law_refs"]:
                            if os.path.exists(f"sources/{ref}"):
                                st.markdown(f"- 📄 `{ref}`")
                            else:
                                st.markdown(f"- 📄 {ref}")

                    if "new_ranks" in suggestions:
                        st.markdown("**Предлагаемые новые ранги:**")
                        nr = suggestions["new_ranks"]
                        col_nr1, col_nr2 = st.columns(2)
                        with col_nr1:
                            # Финансовый
                            fin_val = nr.get('fin', {}).get('value') if isinstance(nr.get('fin'), dict) else nr.get(
                                'fin')
                            fin_reason = nr.get('fin', {}).get('reason') if isinstance(nr.get('fin'), dict) else ""
                            st.metric("💰 Финансовый", fin_val)
                            if fin_reason:
                                st.caption(fin_reason)

                            # Операционный
                            oper_val = nr.get('oper', {}).get('value') if isinstance(nr.get('oper'), dict) else nr.get(
                                'oper')
                            oper_reason = nr.get('oper', {}).get('reason') if isinstance(nr.get('oper'), dict) else ""
                            st.metric("⚙️ Операционный", oper_val)
                            if oper_reason:
                                st.caption(oper_reason)

                            # Юридический
                            jur_val = nr.get('jur', {}).get('value') if isinstance(nr.get('jur'), dict) else nr.get(
                                'jur')
                            jur_reason = nr.get('jur', {}).get('reason') if isinstance(nr.get('jur'), dict) else ""
                            st.metric("⚖️ Юридический", jur_val)
                            if jur_reason:
                                st.caption(jur_reason)

                        with col_nr2:
                            # Репутационный
                            rep_val = nr.get('rep', {}).get('value') if isinstance(nr.get('rep'), dict) else nr.get(
                                'rep')
                            rep_reason = nr.get('rep', {}).get('reason') if isinstance(nr.get('rep'), dict) else ""
                            st.metric("📢 Репутационный", rep_val)
                            if rep_reason:
                                st.caption(rep_reason)

                            # Стратегический
                            strat_val = nr.get('strat', {}).get('value') if isinstance(nr.get('strat'),
                                                                                       dict) else nr.get('strat')
                            strat_reason = nr.get('strat', {}).get('reason') if isinstance(nr.get('strat'),
                                                                                           dict) else ""
                            st.metric("🚩 Стратегический", strat_val)
                            if strat_reason:
                                st.caption(strat_reason)

            # Форма для переоценки
            st.subheader("📊 Новая оценка после инцидента")

            # Определяем значения по умолчанию для ползунков
            default_fin = current_ranks['fin']
            default_oper = current_ranks['oper']
            default_jur = current_ranks['jur']
            default_rep = current_ranks['rep']
            default_strat = current_ranks['strat']

            col_ir1, col_ir2 = st.columns(2)

            with col_ir1:
                new_fin = st.slider(
                    "💰 Финансовый ущерб (1-8)",
                    1, 8, int(default_fin) if default_fin else 1,
                    key="inc_fin"
                )
                new_oper = st.slider(
                    "⚙️ Операционный сбой (1-8)",
                    1, 8, int(default_oper) if default_oper else 1,
                    key="inc_oper"
                )

            with col_ir2:
                new_jur = st.slider(
                    "⚖️ Юридический риск (1-5)",
                    1, 5, int(default_jur) if default_jur else 1,
                    key="inc_jur"
                )
                new_rep = st.slider(
                    "📢 Репутационный ущерб (1-5)",
                    1, 5, int(default_rep) if default_rep else 1,
                    key="inc_rep"
                )
                new_strat = st.slider(
                    "🚩 Стратегический ущерб (1-5)",
                    1, 5, int(default_strat) if default_strat else 1,
                    key="inc_strat"
                )

            # Кнопка сохранения
            if st.button("💾 Зафиксировать событие и переоценить",
                         type="primary", use_container_width=True):
                if event_name:
                    new_ranks = {
                        'fin': new_fin, 'oper': new_oper,
                        'jur': new_jur, 'rep': new_rep, 'strat': new_strat
                    }

                    # Нормализация и итоговый ранг
                    s_scores, total_s = logic.calculate_normalization(new_ranks)
                    final_rank = logic.get_final_rank(total_s)

                    # Сохраняем
                    db.save_evaluation(
                        selected_res_id,
                        new_ranks,
                        total_s,
                        final_rank,
                        trigger=event_name
                    )

                    st.success(f"✅ Событие зафиксировано! Новый ранг: {final_rank}")
                    st.session_state.ai_incident_suggestions = None
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
        df_res = pd.DataFrame(
            resources,
            columns=["ID", "Название", "Категория", "Описание", "Дата создания"]
        )

        st.dataframe(df_res, use_container_width=True)

        # Статистика
        st.subheader("📊 Статистика")
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Всего ресурсов", len(resources))
        with col_stat2:
            categories = df_res["Категория"].value_counts()
            st.metric("Уникальных категорий", len(categories))
        with col_stat3:
            st.metric("Последнее обновление", datetime.now().strftime("%d.%m.%Y"))

        # Детальная информация о ресурсе
        st.markdown("---")
        st.subheader("🔍 Детальная информация о ресурсе")
        res_for_detail = st.selectbox(
            "Выберите ресурс для просмотра истории",
            options=df_res["ID"].tolist(),
            format_func=lambda x: f"{x}: {df_res[df_res['ID'] == x]['Название'].values[0]}",
            key="res_for_detail"
        )

        if res_for_detail:
            history = db.get_evaluation_history(res_for_detail)
            if history:
                df_detail = pd.DataFrame(
                    history,
                    columns=["Дата", "Событие", "Ранг", "Фин", "Опер", "Юр", "Реп", "Страт", "S∑"]
                )
                st.dataframe(df_detail, use_container_width=True)

                # Кнопка экспорта
                csv = df_detail.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Скачать историю оценок (CSV)",
                    csv,
                    f"resource_{res_for_detail}_history.csv",
                    "text/csv",
                    use_container_width=True
                )
            else:
                st.info("ℹ️ Для этого ресурса еще нет оценок.")
    else:
        st.info("ℹ️ База данных пуста")

# Подвал
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; padding: 10px;'>
        © 2025 Система поддержки принятия решений для оценки динамики ценности информационных ресурсов<br>
        Разработано в рамках НИР по специальности 10.05.04
    </div>
    """,
    unsafe_allow_html=True
)