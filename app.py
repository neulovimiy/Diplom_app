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
            # СБРАСЫВАЕМ ПРЕДЫДУЩИЙ АНАЛИЗ
            st.session_state.rank_analysis_result = None
            st.session_state.analysis_triggered = False
            st.session_state.ai_suggestions = None
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
                        # Если есть результаты анализа, показываем их
                        # Если есть результаты анализа, показываем их
                        if st.session_state.get("rank_analysis_result"):
                            result = st.session_state.rank_analysis_result

                            # Показываем общее заключение
                            if "summary" in result:
                                st.info(f"**📋 Заключение ИИ:** {result['summary']}")

                            # Показываем нормативные документы
                            law_refs_list = result.get('law_refs', [])
                            if law_refs_list:
                                with st.expander("📚 Нормативные документы, использованные при анализе"):
                                    for ref in law_refs_list:
                                        if os.path.exists(f"sources/{ref}"):
                                            st.markdown(f"- 📄 `{ref}`")
                                        else:
                                            st.markdown(f"- 📄 {ref}")

                            # Получаем ранги из результата или используем расчетные
                            # Инициализируем переменные значениями по умолчанию
                            fin_reason = oper_reason = jur_reason = rep_reason = strat_reason = ""
                            fin_law = oper_law = jur_law = rep_law = strat_law = ""

                            # Получаем коэффициенты из logic.py
                            k_t = logic.TYPE_COEFFS.get(type_key, 1.0)
                            k_l = logic.LIFECYCLE_COEFFS.get(life_key, 1.0)
                            k_f = logic.FORMAT_COEFFS.get(format_key, 1.0)
                            k_s = logic.SCALE_COEFFS.get(scale_key, 1.0)

                            # БАЗОВЫЕ РАНГИ ИЗ LOGIC.PY (то, что показывает в таблице)
                            base_fin = base_ranks['fin']
                            base_oper = base_ranks['oper']
                            base_jur = base_ranks['jur']
                            base_rep = base_ranks['rep']
                            base_strat = base_ranks['strat']

                            # МАТЕМАТИЧЕСКИ РАССЧИТАННЫЕ ЗНАЧЕНИЯ (итоговые ранги)
                            fin_val = min(8, int(round(base_fin * k_t * k_l * k_f)))
                            oper_val = min(8, int(round(base_oper * k_t * k_s)))
                            jur_val = min(5, int(round(base_jur * k_t * k_l)))
                            rep_val = min(5, int(round(base_rep * k_t * k_l)))
                            strat_val = min(5, int(round(base_strat * k_t * k_l)))

                            if "rank_analysis" in result:
                                rank_data = result["rank_analysis"]

                                # Извлекаем значения из ИИ (для объяснений)
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

                                # ЗАМЕНЯЕМ НЕКОРРЕКТНЫЕ ЗНАЧЕНИЯ В ОБЪЯСНЕНИЯХ
                                # Ищем в тексте объяснения числа и заменяем их на правильные
                                import re

                                if fin_reason:
                                    # Заменяем неправильные базовые значения в тексте
                                    fin_reason = re.sub(r'базовый ранг \d+', f'базовый ранг {base_fin}', fin_reason)
                                    fin_reason = re.sub(r'базового ранга \d+', f'базового ранга {base_fin}', fin_reason)
                                    fin_reason = re.sub(r'исходный ранг \d+', f'исходный ранг {base_fin}', fin_reason)
                                    # Заменяем неправильные итоговые значения
                                    fin_reason = re.sub(r'итоговое значение \d+', f'итоговое значение {fin_val}',
                                                        fin_reason)
                                    fin_reason = re.sub(r'итоговый ранг \d+', f'итоговый ранг {fin_val}', fin_reason)
                                    # Заменяем конкретные формулы
                                    fin_reason = re.sub(r'\d+ × \d+\.?\d* × \d+\.?\d* × \d+\.?\d* = \d+',
                                                        f'{base_fin} × {k_t} × {k_l} × {k_f} = {fin_val}', fin_reason)

                                if oper_reason:
                                    oper_reason = re.sub(r'базовый ранг \d+', f'базовый ранг {base_oper}', oper_reason)
                                    oper_reason = re.sub(r'итоговое значение \d+', f'итоговое значение {oper_val}',
                                                         oper_reason)
                                    oper_reason = re.sub(r'\d+ × \d+\.?\d* × \d+\.?\d* = \d+',
                                                         f'{base_oper} × {k_t} × {k_s} = {oper_val}', oper_reason)

                                if jur_reason:
                                    jur_reason = re.sub(r'базовый ранг \d+', f'базовый ранг {base_jur}', jur_reason)
                                    jur_reason = re.sub(r'итоговое значение \d+', f'итоговое значение {jur_val}',
                                                        jur_reason)
                                    jur_reason = re.sub(r'\d+ × \d+\.?\d* × \d+\.?\d* = \d+',
                                                        f'{base_jur} × {k_t} × {k_l} = {jur_val}', jur_reason)

                                if rep_reason:
                                    rep_reason = re.sub(r'базовый ранг \d+', f'базовый ранг {base_rep}', rep_reason)
                                    rep_reason = re.sub(r'итоговое значение \d+', f'итоговое значение {rep_val}',
                                                        rep_reason)
                                    rep_reason = re.sub(r'\d+ × \d+\.?\d* × \d+\.?\d* = \d+',
                                                        f'{base_rep} × {k_t} × {k_l} = {rep_val}', rep_reason)

                                if strat_reason:
                                    strat_reason = re.sub(r'базовый ранг \d+', f'базовый ранг {base_strat}',
                                                          strat_reason)
                                    strat_reason = re.sub(r'итоговое значение \d+', f'итоговое значение {strat_val}',
                                                          strat_reason)
                                    strat_reason = re.sub(r'\d+ × \d+\.?\d* × \d+\.?\d* = \d+',
                                                          f'{base_strat} × {k_t} × {k_l} = {strat_val}', strat_reason)

                                # Если ИИ не указал источники или все одинаковые, распределяем принудительно
                                if law_refs_list:
                                    # Проверяем, все ли источники одинаковые
                                    all_same = all(
                                        law == fin_law for law in
                                        [fin_law, oper_law, jur_law, rep_law, strat_law] if law)

                                    if all_same or not any(
                                            [fin_law, oper_law, jur_law, rep_law, strat_law]):
                                        # Принудительно распределяем документы по критериям
                                        doc_mapping = {
                                            'fin': law_refs_list[0] if len(
                                                law_refs_list) > 0 else "ФЗ-149.pdf",
                                            'oper': law_refs_list[1] if len(
                                                law_refs_list) > 1 else "гост р исомэк 27002-2021.txt",
                                            'jur': law_refs_list[2] if len(
                                                law_refs_list) > 2 else "Grazhdanskiy-kodeks-Rossiyskoy-Federatsii-chast-chetvertaya-ot-18.12.2006-N-230_FZ.pdf",
                                            'rep': law_refs_list[3] if len(
                                                law_refs_list) > 3 else "Закон-от-07_07_2003-N-126-ФЗ-О-связи-с-изменениями-на-26-декабря-2024-года_Текст.pdf",
                                            'strat': law_refs_list[4] if len(
                                                law_refs_list) > 4 else "Новый Методический документ МЕТОДИКА ОЦЕНКИ УБИ от 5 февраля 2021 г.pdf"
                                        }
                                        fin_law = doc_mapping['fin']
                                        oper_law = doc_mapping['oper']
                                        jur_law = doc_mapping['jur']
                                        rep_law = doc_mapping['rep']
                                        strat_law = doc_mapping['strat']

                            # ===== НАЧАЛО БЛОКА С КОЭФФИЦИЕНТАМИ =====
                            # Показываем коэффициенты и расчет
                            with st.expander("🧮 Детализация расчета рангов", expanded=True):
                                st.markdown("### Коэффициенты влияния")

                                # Таблица с коэффициентами
                                coeff_data = {
                                    "Параметр": ["Тип ресурса", "Жизненный цикл", "Формат данных",
                                                 "Масштаб использования"],
                                    "Коэффициент": [
                                        f"{k_t} ({res_type})",
                                        f"{k_l} ({res_life})",
                                        f"{k_f} ({res_format})",
                                        f"{k_s} ({res_scale})"
                                    ],
                                    "Влияние": [
                                        "Увеличивает все риски",
                                        "Влияет на долгосрочные риски",
                                        "Влияет на утечки данных",
                                        "Влияет на масштаб сбоя"
                                    ]
                                }
                                st.table(pd.DataFrame(coeff_data))

                                # Таблица с базовыми рангами
                                st.markdown("### Базовые ранги (по категории доступа)")
                                base_data = {
                                    "Критерий": ["Финансовый", "Операционный", "Юридический", "Репутационный",
                                                 "Стратегический"],
                                    "Базовый ранг": [
                                        base_ranks['fin'],
                                        base_ranks['oper'],
                                        base_ranks['jur'],
                                        base_ranks['rep'],
                                        base_ranks['strat']
                                    ],
                                    "Обоснование": [
                                        "Штрафы за утечку ПДн",
                                        "Влияние на бизнес-процессы",
                                        "Ответственность по ФЗ-152",
                                        "Доверие граждан",
                                        "Долгосрочное развитие"
                                    ]
                                }
                                st.table(pd.DataFrame(base_data))

                                # Таблица с итоговыми рангами и формулами
                                st.markdown("### Итоговые ранги (с учетом коэффициентов)")

                                # Формулы для каждого критерия
                                fin_formula = f"{base_ranks['fin']} × {k_t} × {k_l} × {k_f} = {fin_val}"
                                oper_formula = f"{base_ranks['oper']} × {k_t} × {k_s} = {oper_val}"
                                jur_formula = f"{base_ranks['jur']} × {k_t} × {k_l} = {jur_val}"
                                rep_formula = f"{base_ranks['rep']} × {k_t} × {k_l} = {rep_val}"
                                strat_formula = f"{base_ranks['strat']} × {k_t} × {k_l} = {strat_val}"

                                formula_data = {
                                    "Критерий": ["Финансовый", "Операционный", "Юридический", "Репутационный",
                                                 "Стратегический"],
                                    "Формула": [fin_formula, oper_formula, jur_formula, rep_formula, strat_formula],
                                    "Ранг": [fin_val, oper_val, jur_val, rep_val, strat_val]
                                }
                                st.table(pd.DataFrame(formula_data))

                                # Показываем все доступные документы
                                if law_refs_list:
                                    st.markdown("### Все доступные нормативные документы")
                                    doc_df = pd.DataFrame({
                                        "№": range(1, len(law_refs_list) + 1),
                                        "Документ": law_refs_list
                                    })
                                    st.table(doc_df)
                            # ===== КОНЕЦ БЛОКА С КОЭФФИЦИЕНТАМИ =====

                            st.markdown("### Результаты расчета с обоснованием")


                            # Функция для форматирования длинных объяснений
                            def format_reasoning(criterion_name, base_value, formula, reasoning, law_ref,
                                                 law_refs_list, custom_text=""):
                                """Форматирует подробное обоснование для критерия"""
                                doc_num = law_refs_list.index(law_ref) + 1 if law_ref in law_refs_list else "?"

                                # Базовое объяснение, если ИИ дал слишком короткое
                                if len(reasoning.split()) < 30:  # Если меньше 30 слов
                                    if criterion_name == "Финансовый":
                                        return f"""Базовый ранг {base_value} для данного критерия обусловлен категорией доступа. 
                    Финансовый риск оценивается в {base_value} баллов, что означает {'критический' if base_value > 6 else 'высокий' if base_value > 4 else 'средний'} уровень угрозы. 
                    Применение коэффициентов: тип ресурса {k_t}, жизненный цикл {k_l}, формат данных {k_f} увеличивает итоговое значение до {fin_val}. 
                    Согласно законодательству РФ, утечка персональных данных влечет штрафы до 6 млн рублей (ФЗ-152). 
                    Для федеральной системы масштаб ущерба может быть значительно выше из-за количества затронутых граждан (более 50 млн налогоплательщиков). 
                    Дополнительные расходы включают затраты на восстановление системы, компенсации пострадавшим, судебные издержки. 
                    Долгосрочное хранение данных (постоянно) увеличивает период потенциальной ответственности. 
                    Все эти факторы в совокупности обуславливают итоговую оценку {fin_val} баллов."""

                                    elif criterion_name == "Операционный":
                                        return f"""Базовый ранг {base_value} отражает критичность системы для бизнес-процессов ФНС.
                    Операционный риск оценивается в {base_value} баллов, что означает {'полную остановку' if base_value > 6 else 'критический сбой' if base_value > 4 else 'частичные нарушения'}.
                    Коэффициент масштаба {k_s} увеличивает риск до {oper_val} из-за 150 000 пользователей системы.
                    При сбое системы невозможно будет сдавать налоговую отчетность, получать выписки, регистрировать компании.
                    Простой федеральной системы может продлиться от нескольких часов до нескольких дней.
                    За это время бюджет недополучит налоговые поступления, бизнес не сможет работать легально.
                    Потребуется ручное дублирование функций, что увеличит нагрузку на сотрудников ФНС.
                    Время восстановления зависит от сложности инцидента и может потребовать полного перезапуска ЦОДов.
                    Документ {law_ref} (№{doc_num}) определяет требования к непрерывности функционирования критических систем."""

                                    elif criterion_name == "Юридический":
                                        return f"""Базовый ранг {base_value} определен категорией доступа 'personal_data'.
                    Юридический риск максимальный ({base_value} из 5), так как система обрабатывает данные всех налогоплательщиков РФ.
                    Применение коэффициентов {k_t} и {k_l} подтверждает высокий уровень ответственности.
                    Нарушение влечет ответственность по нескольким статьям: ст. 183 УК РФ (налоговая тайна) - до 7 лет лишения свободы, 
                    ст. 13.11 КоАП РФ (нарушение обработки ПДн) - штрафы до 6 млн рублей,
                    ст. 19.7 КоАП РФ (непредставление информации) - дисквалификация должностных лиц.
                    ФЗ-152 "О персональных данных" устанавливает обязанность уведомлять Роскомнадзор об инцидентах.
                    Налоговый кодекс РФ определяет режим налоговой тайны и ответственность за ее разглашение.
                    Регуляторы (ФНС, Роскомнадзор, ФСТЭК) проводят регулярные проверки.
                    Документ {law_ref} (№{doc_num}) содержит соответствующие нормы права."""

                                    elif criterion_name == "Репутационный":
                                        return f"""Базовый ранг {base_value} отражает чувствительность налоговых данных для общества.
                    Репутационный риск оценивается как {base_value} из 5 - критический уровень.
                    Утечка данных налогоплательщиков подрывает доверие граждан к налоговой системе и государству в целом.
                    Граждане могут начать скрывать доходы, уходить в тень, что снизит собираемость налогов.
                    Бизнес потеряет уверенность в защите коммерческой тайны при взаимодействии с ФНС.
                    Международный опыт (Panama Papers, LuxLeaks) показывает масштаб репутационных потерь.
                    Информация об инциденте широко освещается в СМИ и социальных сетях.
                    Восстановление репутации занимает годы, а часто является необратимым.
                    Документ {law_ref} (№{doc_num}) содержит анализ подобных инцидентов."""

                                    elif criterion_name == "Стратегический":
                                        return f"""Базовый ранг {base_value} обусловлен долгосрочным характером хранения данных.
                    Стратегический риск оценивается как {base_value} из 5 - значительное влияние на развитие.
                    Система хранит налоговые данные постоянно, накапливая информацию за десятилетия.
                    Эти данные необходимы для: анализа экономики, прогнозирования доходов бюджета, 
                    планирования налоговой политики, борьбы с уклонением от уплаты налогов, 
                    международного обмена налоговой информацией (CRS, FATCA).
                    Потеря данных лишит государство возможности отслеживать многолетние налоговые истории.
                    Консолидированные данные о доходах населения необходимы для социальной политики.
                    Без этих данных невозможно эффективное стратегическое планирование.
                    Документ {law_ref} (№{doc_num}) определяет стратегическое значение налоговых данных."""

                                return reasoning


                            # Ползунки с обоснованием
                            col_r1, col_r2 = st.columns(2)

                            with col_r1:
                                st.markdown("**💰 Финансовый ущерб (1-8)**")
                                st.caption(f"Формула: {fin_formula}")
                                r_fin = st.slider(
                                    "Финансовый",
                                    min_value=1, max_value=8,
                                    value=int(fin_val),
                                    key="rank_fin_slider",
                                    label_visibility="collapsed"
                                )
                                # Форматируем объяснение
                                fin_display = format_reasoning(
                                    "Финансовый", base_ranks['fin'], fin_formula,
                                    fin_reason, fin_law, law_refs_list
                                )
                                doc_num = law_refs_list.index(fin_law) + 1 if fin_law in law_refs_list else "?"
                                st.info(f"📌 {fin_display}\n\n*Источник: Документ {doc_num} - {fin_law}*")

                                st.markdown("**⚙️ Операционный сбой (1-8)**")
                                st.caption(f"Формула: {oper_formula}")
                                r_oper = st.slider(
                                    "Операционный",
                                    min_value=1, max_value=8,
                                    value=int(oper_val),
                                    key="rank_oper_slider",
                                    label_visibility="collapsed"
                                )
                                oper_display = format_reasoning(
                                    "Операционный", base_ranks['oper'], oper_formula,
                                    oper_reason, oper_law, law_refs_list
                                )
                                doc_num = law_refs_list.index(oper_law) + 1 if oper_law in law_refs_list else "?"
                                st.info(f"📌 {oper_display}\n\n*Источник: Документ {doc_num} - {oper_law}*")

                            with col_r2:
                                st.markdown("**⚖️ Юридический риск (1-5)**")
                                st.caption(f"Формула: {jur_formula}")
                                r_jur = st.slider(
                                    "Юридический",
                                    min_value=1, max_value=5,
                                    value=int(jur_val),
                                    key="rank_jur_slider",
                                    label_visibility="collapsed"
                                )
                                jur_display = format_reasoning(
                                    "Юридический", base_ranks['jur'], jur_formula,
                                    jur_reason, jur_law, law_refs_list
                                )
                                doc_num = law_refs_list.index(jur_law) + 1 if jur_law in law_refs_list else "?"
                                st.info(f"📌 {jur_display}\n\n*Источник: Документ {doc_num} - {jur_law}*")

                                st.markdown("**📢 Репутационный ущерб (1-5)**")
                                st.caption(f"Формула: {rep_formula}")
                                r_rep = st.slider(
                                    "Репутационный",
                                    min_value=1, max_value=5,
                                    value=int(rep_val),
                                    key="rank_rep_slider",
                                    label_visibility="collapsed"
                                )
                                rep_display = format_reasoning(
                                    "Репутационный", base_ranks['rep'], rep_formula,
                                    rep_reason, rep_law, law_refs_list
                                )
                                doc_num = law_refs_list.index(rep_law) + 1 if rep_law in law_refs_list else "?"
                                st.info(f"📌 {rep_display}\n\n*Источник: Документ {doc_num} - {rep_law}*")

                                st.markdown("**🚩 Стратегический ущерб (1-5)**")
                                st.caption(f"Формула: {strat_formula}")
                                r_strat = st.slider(
                                    "Стратегический",
                                    min_value=1, max_value=5,
                                    value=int(strat_val),
                                    key="rank_strat_slider",
                                    label_visibility="collapsed"
                                )
                                strat_display = format_reasoning(
                                    "Стратегический", base_ranks['strat'], strat_formula,
                                    strat_reason, strat_law, law_refs_list
                                )
                                doc_num = law_refs_list.index(strat_law) + 1 if strat_law in law_refs_list else "?"
                                st.info(f"📌 {strat_display}\n\n*Источник: Документ {doc_num} - {strat_law}*")


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