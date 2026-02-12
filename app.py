# app.py
import streamlit as st
import database as db
import modules.ai_analyst as ai
import logic
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
from io import BytesIO
import os

st.set_page_config(page_title="СППР Оценка ИР", layout="wide", page_icon="🛡️")

if "ai_cache" not in st.session_state: st.session_state["ai_cache"] = None
if "impact_cache" not in st.session_state: st.session_state["impact_cache"] = None


def create_pdf_report(res_name, res_cat, res_desc, history_df):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_left_margin(15);
    pdf.set_right_margin(15)

    font_path = "DejaVuSans.ttf"
    if os.path.exists(font_path):
        pdf.add_font("DejaVu", "", font_path);
        fn = "DejaVu"
        pdf.set_font("DejaVu", size=12)
    else:
        fn = "Arial"; pdf.set_font("Arial", size=12)

    pdf.set_font(fn, size=18);
    pdf.cell(0, 15, txt="ОТЧЕТ О ЦЕННОСТИ ИР", ln=True, align='C')
    pdf.set_font(fn, size=11);
    pdf.set_x(15)
    pdf.cell(0, 10, txt=f"Ресурс: {res_name} | Категория: {res_cat}", ln=True)
    pdf.multi_cell(0, 7, txt=f"Описание: {res_desc}");
    pdf.ln(5)

    if not history_df.empty:
        plt.figure(figsize=(10, 4))
        plt.plot(history_df["Дата"], history_df["Общий"], marker='o', color='#1f77b4')
        plt.title("Динамика ранга ценности");
        plt.grid(True, alpha=0.3)
        img_buf = BytesIO();
        plt.savefig(img_buf, format='png', bbox_inches='tight');
        plt.close()
        pdf.set_x(15);
        pdf.image(img_buf, w=180);
        pdf.ln(10)

    pdf.set_font(fn, size=12);
    pdf.set_x(15);
    pdf.cell(0, 10, txt="История экспертных оценок:", ln=True)
    pdf.set_font(fn, size=9)
    for _, row in history_df.iterrows():
        line = f"{str(row['Дата'])[:10]} | {row['Событие']} | Ранг: {row['Общий']} [Ф:{row['Фин']}, О:{row['Опер']}, Ю:{row['Юр']}, Р:{row['Реп']}, С:{row['Страт']}]"
        pdf.set_x(15);
        pdf.multi_cell(0, 8, txt=line, border='B');
        pdf.ln(1)
    return bytes(pdf.output())


st.title("🛡️ СППР: Оценка и мониторинг ценности ИР")
tab1, tab2, tab3 = st.tabs(["📂 Реестр ресурсов", "📊 Анализ и Оценка", "📄 Отчетность"])

with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.header("Добавить ресурс")
        n_n = st.text_input("Название", key="reg_n")
        n_d = st.text_area("Описание", key="reg_d")
        n_c = st.selectbox("Категория", ["Общедоступная", "Персональные данные", "Коммерческая тайна",
                                         "Интеллектуальная собственность"], key="reg_c")
        if st.button("💾 Сохранить", key="reg_b"):
            if n_n and n_d:
                db.add_resource(n_n, n_d, n_c);
                st.success("Готово!");
                st.rerun()
    with c2:
        st.header("База данных")
        reg_data = db.get_all_resources_full()
        if reg_data:
            st.dataframe(pd.DataFrame(reg_data, columns=["ID", "Название", "Категория", "Описание", "Создан"]),
                         use_container_width=True, hide_index=True)

with tab2:
    all_r = db.get_all_resources_full()
    if not all_r:
        st.warning("База пуста.")
    else:
        r_map = {f"{r[0]}: {r[1]}": r[0] for r in all_r}
        sel = st.selectbox("Выберите ИР:", ["-- не выбрано --"] + list(r_map.keys()), key="ev_sel")
        if sel != "-- не выбрано --":
            rid = r_map[sel]
            rname, rdesc, rcat = db.get_resource_by_id(rid)
            hist = db.get_evaluation_history(rid)
            mem = db.get_recent_evaluations_for_learning(5)

            if hist:
                l = hist[-1];
                m1, m2, m3, m4, m5, m6 = st.columns(6)
                m1.metric("ИТОГ", l[2]);
                m2.metric("Фин", l[3]);
                m3.metric("Опер", l[4]);
                m4.metric("Юр", l[5]);
                m5.metric("Реп", l[6]);
                m6.metric("Страт", l[7])
                cur_r = (l[2], l[3], l[4], l[5], l[6], l[7])
            else:
                cur_r = (1, 1, 1, 1, 1, 1)

            st.markdown("---")
            ca1, ca2 = st.columns(2)
            with ca1:
                if st.button("🔍 Анализ ИИ", key="b_ai1"):
                    with st.spinner("Анализ..."):
                        st.session_state["ai_cache"] = ai.get_ai_recommendation(rname, rdesc, rcat, mem)
                        st.session_state["impact_cache"] = None
            with ca2:
                e_v = st.text_input("Событие:", key="e_v_txt")
                if st.button("🔮 Прогноз", key="b_ai2"):
                    if e_v:
                        with st.spinner("Прогнозирование..."):
                            st.session_state["impact_cache"] = ai.analyze_event_impact(rname, cur_r, e_v, mem)
                            st.session_state["ai_cache"] = None

            if st.session_state["ai_cache"]: st.info(st.session_state["ai_cache"])
            if st.session_state["impact_cache"]: st.warning(st.session_state["impact_cache"])

            st.markdown("---")
            dv = hist[-1] if hist else [0, 0, 1, 1, 1, 1, 1, 1]
            s1, s2 = st.columns(2)
            with s1:
                rf = st.slider("Фин (1-8)", 1, 8, int(dv[3]), key="sf")
                ro = st.slider("Опер (1-8)", 1, 8, int(dv[4]), key="so")
                rs = st.slider("Страт (1-5)", 1, 5, int(dv[7]), key="ss")
            with s2:
                rj = st.slider("Юр (1-5)", 1, 5, int(dv[5]), key="sj")
                rr = st.slider("Реп (1-5)", 1, 5, int(dv[6]), key="sr")
                tr = st.selectbox("Триггер", ["Плановая оценка", "Утечка", "Сбой", "Другое"], key="st")
                ft = st.text_input("Уточнение:", value="Инцидент", key="st_m") if tr == "Другое" else tr

            if st.button("✅ Сохранить", key="b_save"):
                rks = {'fin': rf, 'oper': ro, 'jur': rj, 'rep': rr, 'strat': rs}
                _, ts = logic.calculate_normalization(rks)
                fr = logic.get_final_rank(ts)
                db.save_evaluation(rid, rks, ts, fr, ft)
                st.session_state["ai_cache"] = None;
                st.session_state["impact_cache"] = None
                st.rerun()

            if hist:
                st.markdown("---")
                st.subheader("📈 Мониторинг")
                hdf = pd.DataFrame(hist, columns=["Дата", "Событие", "Общий", "Фин", "Опер", "Юр", "Реп", "Страт", "S"])
                st.caption("Общий ранг ценности")
                st.line_chart(hdf.set_index("Дата")["Общий"])

                g1, g2, g3 = st.columns(3)
                with g1: st.caption("Финансы"); st.line_chart(hdf.set_index("Дата")["Фин"])
                with g2: st.caption("Операции"); st.line_chart(hdf.set_index("Дата")["Опер"])
                with g3: st.caption("Юридический"); st.line_chart(hdf.set_index("Дата")["Юр"])
                g4, g5, _ = st.columns(3)
                with g4: st.caption("Репутация"); st.line_chart(hdf.set_index("Дата")["Реп"])
                with g5: st.caption("Стратегия"); st.line_chart(hdf.set_index("Дата")["Страт"])

                # ТАБЛИЦА (Теперь она здесь)
                st.markdown("---")
                st.subheader("📊 История изменений (Таблица)")
                st.dataframe(hdf, use_container_width=True, hide_index=True)

with tab3:
    st.header("📄 Отчетность")
    all_res = db.get_all_resources_full()
    if all_res:
        rm = {f"ID {r[0]}: {r[1]}": r[0] for r in all_res}
        t = st.selectbox("Ресурс для отчета:", ["-- выберите --"] + list(rm.keys()), key="rep_s")
        if t != "-- выберите --":
            tid = rm[t];
            tn, td, tc = db.get_resource_by_id(tid);
            th = db.get_evaluation_history(tid)
            if th:
                hdf_r = pd.DataFrame(th, columns=["Дата", "Событие", "Общий", "Фин", "Опер", "Юр", "Реп", "Страт", "S"])
                st.line_chart(hdf_r.set_index("Дата")["Общий"])
                pdf_o = create_pdf_report(tn, tc, td, hdf_r)
                st.download_button("📥 СКАЧАТЬ PDF", data=pdf_o, file_name=f"Report_{tid}.pdf", mime="application/pdf",
                                   key="dl_b")