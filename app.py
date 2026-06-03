import streamlit as st
import os
import json
import datetime
from modules.extractor import extract_text
from modules.structure_checker import check_structure, extract_document_headings
from modules.introduction_checker import check_introduction
from modules.llm_analyzer import analyze_intro
from modules.text_splitter import extract_intro
from modules.method_base import load_method_base
from modules.llm_structure import analyze_structure
from modules.conclusion_splitter import extract_conclusion
from modules.llm_conclusion import analyze_conclusion
from modules.literature_splitter import extract_literature, analyze_literature_stats
from modules.llm_literature import analyze_literature
from modules.gost_checker import check_gost

# =====================
# ИСТОРИЯ ПРОВЕРОК
# =====================

HISTORY_PATH = "data/history/history.json"


def load_history():
    if not os.path.exists(HISTORY_PATH):
        return []

    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return []


def save_history_item(item):
    os.makedirs("data/history", exist_ok=True)

    history = load_history()

    history.append(item)

    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

# Настройка страницы
st.set_page_config(
    page_title="Аналитическая нейросеть МИРЭА",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📚 Аналитическая нейросеть для проверки студенческих работ")
st.markdown("### РТУ МИРЭА — Институт технологий управления")

# Блок ввода метаданных (по ТЗ 4.1.1 и 4.2)
with st.sidebar:
    st.header("Метаданные работы")

    student_name = st.text_input("ФИО студента")

    group = st.text_input("Группа")

    directions = {
        "01.03.05 Статистика": "01.03.05",
        "27.03.05 Инноватика": "27.03.05",
        "38.03.01 Экономика": "38.03.01",
        "38.03.02 Менеджмент": "38.03.02",
        "38.03.03 Управление персоналом": "38.03.03",
        "38.03.04 Государственное и муниципальное управление": "38.03.04",
        "38.03.05 Бизнес-информатика": "38.03.05",
        "40.03.01 Юриспруденция": "40.03.01",
        "46.03.02 Документоведение и архивоведение": "46.03.02"
    }

    selected_direction = st.selectbox(
        "Направление подготовки",
        list(directions.keys())
    )

    direction_code = directions[selected_direction]

    work_type = st.selectbox(
        "Тип работы",
        ["Курсовая работа", "Дипломная работа"]
    )

    topic = st.text_area(
        "Тема работы",
        height=100
    )

    uploaded_method = st.file_uploader(
        "Дополнительная методичка студента (.docx или .pdf)",
        type=["docx", "pdf"],
        key="uploaded_method"
    )

    uploaded_method_path = None

    if uploaded_method is not None:
        os.makedirs("temp", exist_ok=True)

        uploaded_method_path = os.path.join(
            "temp",
            uploaded_method.name
        )

        with open(uploaded_method_path, "wb") as f:
            f.write(uploaded_method.getbuffer())

        st.success(
            "✅ Дополнительная методичка загружена"
        )

    method_text, direction_exists = load_method_base(
        direction=direction_code,
        topic=topic,
        group=group,
        uploaded_method_path=uploaded_method_path
    )

    if not direction_exists:
        st.warning(
            "⚠️ Методические указания для данного направления не найдены.\n"
            "Анализ будет выполнен по Нормоконтролю и загруженной методичке."
        )
    st.divider()
 
    with st.expander("📚 История проверок"):
        history = load_history()

        if not history:
            st.info("История пока пустая")

        else:
            for item in reversed(history[-10:]):
                st.markdown(
                    f"""
                **{item.get('student_name', 'Не указано')}**  
                {item.get('date', '')}  
                Балл: **{item.get('total_score', 0)}/100**  
                {item.get('verdict', '')}
                ---
                """
                )

uploaded_file = st.file_uploader(
    "Загрузите студенческую работу (.docx или .pdf)",
    type=["docx", "pdf"]
)

if uploaded_file:
    st.success(f"✅ Файл успешно загружен: **{uploaded_file.name}**")
    
    try:
        # Извлечение текста
        text = extract_text(uploaded_file, uploaded_file.name)
        st.session_state["current_text"] = text
        st.text_area(
            "DEBUG: первые 8000 символов извлечённого текста",
            text[:8000],
            height=500
        )

        full_method_text = method_text

        if not text or not text.strip():
            st.warning("⚠️ Не удалось извлечь текст из файла. Возможно, PDF является сканом (без текстового слоя) или файл пустой.")
        else:
            st.subheader("📄 Извлечённый текст")
            st.text_area("Текст работы (первые 5000 символов)", text[:5000], height=400)
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Длина текста:** {len(text):,} символов")
            with col2:
                st.info(f"**Примерно страниц:** {len(text) // 1800 + 1}")
    
    except Exception as e:
        st.error(f"❌ Ошибка при обработке файла: {str(e)}")
        st.info("Поддерживаемые форматы: .docx и .pdf с текстовым слоем.")

# Кнопка для следующего шага (пока заглушка)
if st.button("Проверить структуру работы →", type="primary"):

    result = check_structure(text)

    if "results" not in result:
        st.error("Ошибка: функция check_structure вернула неправильный формат")
    else:
        st.subheader("📊 Проверка структуры работы")

        for section, exists in result["results"].items():
            if exists:
                st.success(f"✔ Раздел «{section}» найден")
            else:
                st.error(f"✘ Раздел «{section}» отсутствует")

        if result.get("missing"):
            st.warning("❗ Отсутствуют: " + ", ".join(result["missing"]))
        else:
            st.success("✅ Все разделы есть")
if st.button("AI-анализ введения 🤖"):

    text = st.session_state.get("current_text", "")

    if not text or not text.strip():

        if uploaded_file is not None:
            uploaded_file.seek(0)
            text = extract_text(uploaded_file, uploaded_file.name)
            st.session_state["current_text"] = text

    if not text or not text.strip():
        st.error("Не удалось получить текст работы. Загрузите файл заново.")
        st.stop()

    intro_text = extract_intro(text)

    with st.spinner("Нейросеть анализирует введение..."):
        full_method_text = method_text

        result = analyze_intro(
            intro_text,
            full_method_text
        )

        if not result:
            result = "Ошибка: модель не вернула ответ."

        result = str(result)

        result = result.replace("<br>", "\n")
        result = result.replace("|", "")

    st.subheader("🤖 Анализ введения")

    blocks = result.split("\n\n")

    for block in blocks:

        block_lower = block.lower()

        formatted_block = block.replace("\n", "  \n")

        if "нет" in block_lower:
            st.error(formatted_block)

        elif "частично" in block_lower or "возможно" in block_lower:
            st.warning(formatted_block)

        elif "да" in block_lower:
            st.success(formatted_block)

        else:
            st.info(formatted_block)
            
if st.button("AI-анализ структуры 🤖"):

    with st.spinner(
        "Нейросеть анализирует структуру работы..."
    ):

        structure_result = check_structure(text)
        document_headings = extract_document_headings(text)

        structure_text = ""

        for section, exists in structure_result["results"].items():

            structure_text += (
                f"{section}: {exists}\n"
            )

        result = analyze_structure(
            structure_text,
            full_method_text
        )

        result = result.replace(
            "Комментарий: ",
            "Комментарий:\n"
        )

    st.subheader("🤖 AI-анализ структуры")

    blocks = result.split("\n\n")

    for block in blocks:

        formatted_block = block.replace(
            "\n",
            "  \n"
        )

        first_line = block.split("\n")[0].lower()

        if (
            ": нет" in first_line
            or first_line.startswith("проблемы")
        ):

            st.error(formatted_block)

        elif (
            ": частично" in first_line
            or ": возможно" in first_line
        ):

            st.warning(formatted_block)

        elif ": да" in first_line:

            st.success(formatted_block)

        else:

            st.info(formatted_block)
if st.button("AI-анализ заключения 🤖"):

    conclusion_text = extract_conclusion(text)
    
    if not conclusion_text:

        st.error(
            "Не удалось найти заключение"
        )

    else:

        with st.spinner(
            "Нейросеть анализирует заключение..."
        ):

            result = analyze_conclusion(
                conclusion_text,
                full_method_text
            )

            result = result.replace(
                "Комментарий: ",
                "Комментарий:\n"
            )

        st.subheader(
            "🤖 Анализ заключения"
        )

        blocks = result.split("\n\n")

        for block in blocks:

            formatted_block = block.replace(
                "\n",
                "  \n"
            )

            first_line = (
                block.split("\n")[0]
                .lower()
            )

            if (
                ": нет" in first_line
                or first_line.startswith(
                    "что исправить"
                )
            ):

                st.error(formatted_block)

            elif (
                ": частично" in first_line
                or ": возможно" in first_line
            ):

                st.warning(formatted_block)

            elif ": да" in first_line:

                st.success(formatted_block)

            else:

                st.info(formatted_block)
if st.button("AI-анализ литературы 🤖"):

    literature_text = extract_literature(text)

    if not literature_text:

        st.error(
            "Не удалось найти список литературы"
        )

    else:

        with st.spinner(
            "Нейросеть анализирует литературу..."
        ):

            result = analyze_literature(
                literature_text,
                full_method_text
            )

            result = result.replace(
                "Комментарий: ",
                "Комментарий:\n"
            )

        st.subheader(
            "🤖 Анализ литературы"
        )

        blocks = result.split("\n\n")

        for block in blocks:

            formatted_block = block.replace(
                "\n",
                "  \n"
            )

            first_line = (
                block.split("\n")[0]
                .lower()
            )

            if (
                ": нет" in first_line
                or first_line.startswith(
                    "что исправить"
                )
            ):

                st.error(formatted_block)

            elif (
                ": частично" in first_line
                or ": возможно" in first_line
            ):

                st.warning(formatted_block)

            elif ": да" in first_line:

                st.success(formatted_block)

            else:

                st.info(formatted_block)
if st.button("Проверка ГОСТ оформления 📑"):
    if uploaded_file is None:
        st.warning("Сначала загрузите файл")

    elif not uploaded_file.name.lower().endswith(".docx"):
        st.info(
            "Проверка ГОСТ оформления доступна только для DOCX. "
            "PDF будет использоваться для текстового анализа, структуры, введения, "
            "заключения и списка литературы."
        )
    else:
        try:
            uploaded_file.seek(0)

            with open("temp.docx", "wb") as f:
                f.write(uploaded_file.read())

            result = check_gost("temp.docx", full_method_text)

            if "error" in result:
                st.error(result["error"])
                st.stop()

            st.subheader("📑 Результат проверки ГОСТ")

            checks = [
                ("Шрифт", result["font"]["status"]),
                ("Размер шрифта", result["size"]["status"]),
                ("Межстрочный интервал", result["spacing"]["status"]),
                ("Выравнивание текста", result["alignment"]["status"]),
                ("Красная строка", result["indent"]["status"]),
                ("Заголовки", result["headings"]["status"]),
                ("Таблицы", result["tables"]["status"]),
                ("Рисунки", result["figures"]["status"])
            ]

            all_good = all(status for _, status in checks)

            if all_good:
                st.success("🎉 Общее соответствие ГОСТ: ПОЛНОЕ")
            else:
                st.error("⚠️ Общее соответствие ГОСТ: ТРЕБУЕТ ДОРАБОТКИ")

            for name, status in checks:
                if status:
                    st.success(f"✅ {name}: соответствует")
                else:
                    st.error(f"❌ {name}: НЕ соответствует")

            # Детальные ошибки по заголовкам
            if not result["headings"]["status"] and result["headings"]["errors"]:
                st.markdown("**Ошибки в заголовках:**")
                for err in result["headings"]["errors"]:
                    st.error(err)
            
            if not result["tables"]["status"]:

                st.markdown("**Ошибки в таблицах:**")

                for err in result["tables"]["errors"]:
                    st.error(err)

            if not result["figures"]["status"]:

                st.markdown("**Ошибки в рисунках:**")

                for err in result["figures"]["errors"]:
                    st.error(err)

        except Exception as e:
            st.error(f"Ошибка: {str(e)}")

if st.button("🚀 Полный анализ работы", type="primary", use_container_width=True):
    if uploaded_file is None:
        st.error("Сначала загрузите файл!")
    else:
        with st.spinner("Выполняется полный анализ работы... (это может занять пару минут)"):
            
            uploaded_file.seek(0)
            text = extract_text(uploaded_file, uploaded_file.name)

            # =====================
            # ЗАПУСКАЕМ ВСЕ ПРОВЕРКИ
            # =====================
            uploaded_file.seek(0)

            gost_result = None

            if uploaded_file.name.lower().endswith(".docx"):

                uploaded_file.seek(0)

                with open("temp.docx", "wb") as f:
                    f.write(uploaded_file.read())

                gost_result = check_gost("temp.docx", full_method_text)

                if "error" in gost_result:
                    st.error(gost_result["error"])
                    st.stop()

            else:

                gost_result = {
                    "font": {"status": None},
                    "size": {"status": None},
                    "spacing": {"status": None},
                    "alignment": {"status": None},
                    "indent": {"status": None},
                    "headings": {"status": None},
                    "pdf_notice": (
                        "ГОСТ-оформление для PDF не проверялось. "
                        "PDF используется для текстового анализа."
                    )
                }

            if "error" in gost_result:
                st.error(gost_result["error"])
                st.stop()
            
            structure_result = check_structure(text)
            document_headings = extract_document_headings(text)
            structure_input = f"""
            Результат программной проверки:
            {structure_result}

            Реальные заголовки и разделы документа:
            {document_headings}
            """

            structure_llm = analyze_structure(
                structure_input,
                full_method_text
            )
            intro_result = check_introduction(text)
            
            # LLM анализы
            intro_text = extract_intro(text)

            if not intro_text:
                intro_text = text[:12000]

            intro_llm = analyze_intro(
                intro_text,
                full_method_text
            )

            conclusion_text = extract_conclusion(text)
            conclusion_llm = analyze_conclusion(conclusion_text, full_method_text) if conclusion_text else "Не найдено заключение"

            literature_text = extract_literature(text)
            literature_stats = analyze_literature_stats(literature_text)

            literature_context = f"""
            Статистика списка литературы:
            Количество источников: {literature_stats["sources_count"]}
            Самый старый год: {literature_stats["oldest_year"]}
            Самый новый год: {literature_stats["latest_year"]}
            Количество интернет-источников: {literature_stats["internet_sources_count"]}
            """

            literature_llm = analyze_literature(
                literature_context + "\n\n" + literature_text,
                full_method_text
            ) if literature_text else "Не найден список литературы"

            structure_input = f"""
            Результат программной проверки:
            {structure_result}

            Реальные заголовки и разделы документа:
            {document_headings}
            """

            structure_llm = analyze_structure(
                structure_input,
                full_method_text
            )

            # =====================
            # ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ВЫВОДА
            # =====================

            def get_status_color(block):
                first_line = block.strip().splitlines()[0].lower()

                if "частично" in first_line:
                    return "warning"

                if "нет" in first_line:
                    return "error"

                if "да" in first_line:
                    return "success"

                lower = block.lower()

                if (
                    "отсутствует" in lower
                    or "требуется" in lower
                    or "исправить" in lower
                ):
                    return "error"

                if (
                    "возможно" in lower
                    or "замечания" in lower
                ):
                    return "warning"

                return "info"


            def show_colored_block(block):
                block = block.strip()

                if not block:
                    return

                color = get_status_color(block)

                if color == "success":
                    st.success(block)

                elif color == "warning":
                    st.warning(block)

                elif color == "error":
                    st.error(block)

                else:
                    st.info(block)


            def split_llm_blocks(text):
                if not text:
                    return []

                lines = [
                    line.strip()
                    for line in text.splitlines()
                    if line.strip()
                ]

                blocks = []
                current_block = []

                for line in lines:
                    is_new_block = (
                        ":" in line
                        and not line.lower().startswith("комментарий")
                        and not line[0].isdigit()
                    )

                    if is_new_block and current_block:
                        blocks.append("\n".join(current_block))
                        current_block = [line]
                    else:
                        current_block.append(line)

                if current_block:
                    blocks.append("\n".join(current_block))

                return blocks


            # =====================
            # ОБЩАЯ ОЦЕНКА
            # =====================

            st.success("✅ Полный анализ завершён!")

            st.subheader("📊 Общая оценка работы")

            is_docx = uploaded_file.name.lower().endswith(".docx")

            if is_docx:
                gost_ok = all([
                    gost_result.get(k, {}).get("status", False)
                    for k in [
                        "font",
                        "size",
                        "spacing",
                        "alignment",
                        "indent",
                        "headings"
                        "tables",
                        "figures"
                    ]
                ])
            else:
                gost_ok = None

            structure_ok = all(
                structure_result.get("results", {}).values()
            )

            st.session_state["analysis_done"] = True
            st.session_state["gost_result"] = gost_result
            st.session_state["structure_result"] = structure_result
            st.session_state["intro_llm"] = intro_llm
            st.session_state["conclusion_llm"] = conclusion_llm
            st.session_state["literature_llm"] = literature_llm
            st.session_state["structure_llm"] = structure_llm
            st.session_state["gost_ok"] = gost_ok
            st.session_state["structure_ok"] = structure_ok
            st.session_state["literature_stats"] = literature_stats
            st.session_state["document_headings"] = document_headings

            # =====================
            # БАЛЛЬНАЯ ОЦЕНКА
            # =====================

            def llm_score(text):
                if not text:
                    return 0

                lower = text.lower()

                yes_count = lower.count(": да")
                partial_count = lower.count(": частично")
                no_count = lower.count(": нет")

                total = yes_count + partial_count + no_count

                if total == 0:
                    return 10

                score = (
                    yes_count * 20
                    + partial_count * 10
                    + no_count * 0
                ) / total

                return round(score)


            if gost_ok is None:
                gost_score = 0
            else:
                gost_checks = [
                    gost_result.get(k, {}).get("status", False)
                    for k in [
                        "font",
                        "size",
                        "spacing",
                        "alignment",
                        "indent",
                        "headings"
                    ]
                ]

                gost_score = round(
                    sum(1 for item in gost_checks if item) / len(gost_checks) * 20
                )

            structure_values = list(
                structure_result.get("results", {}).values()
            )

            if structure_values:
                structure_score = round(
                    sum(1 for item in structure_values if item) / len(structure_values) * 20
                )
            else:
                structure_score = 0

            intro_score = llm_score(intro_llm)
            conclusion_score = llm_score(conclusion_llm)
            literature_score = llm_score(literature_llm)

            total_score = (
                gost_score
                + structure_score
                + intro_score
                + conclusion_score
                + literature_score
            )

            if total_score >= 85:
                verdict = "🟢 Готово к сдаче"
            elif total_score >= 70:
                verdict = "🟡 Нужны небольшие правки"
            elif total_score >= 50:
                verdict = "🟠 Требует доработки"
            else:
                verdict = "🔴 Требует серьёзной переработки"

            st.session_state["total_score"] = total_score
            st.session_state["verdict"] = verdict
            st.session_state["gost_score"] = gost_score
            st.session_state["structure_score"] = structure_score
            st.session_state["intro_score"] = intro_score
            st.session_state["conclusion_score"] = conclusion_score
            st.session_state["literature_score"] = literature_score
            st.session_state["literature_stats"] = literature_stats
            st.session_state["document_headings"] = document_headings

            history_item = {
                "date": datetime.datetime.now().strftime("%d.%m.%Y %H:%M"),
                "student_name": student_name or "Не указано",
                "group": group or "Не указана",
                "direction": selected_direction,
                "work_type": work_type,
                "topic": topic or "Не указана",
                "file_name": uploaded_file.name,
                "total_score": total_score,
                "verdict": verdict,
                "gost_score": gost_score,
                "structure_score": structure_score,
                "intro_score": intro_score,
                "conclusion_score": conclusion_score,
                "literature_score": literature_score
            }

            save_history_item(history_item)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Итоговый балл",
                    f"{total_score}/100"
                )

            with col2:
                st.metric(
                    "Оформление",
                    f"{gost_score}/20" if gost_ok is not None else "PDF"
                )

            with col3:
                st.metric(
                    "Общий вердикт",
                    verdict
                )

            st.progress(total_score / 100)

            st.markdown("### Детализация баллов")

            score_col1, score_col2, score_col3, score_col4, score_col5 = st.columns(5)

            with score_col1:
                st.metric("ГОСТ", f"{gost_score}/20" if gost_ok is not None else "—")

            with score_col2:
                st.metric("Структура", f"{structure_score}/20")

            with score_col3:
                st.metric("Введение", f"{intro_score}/20")

            with score_col4:
                st.metric("Заключение", f"{conclusion_score}/20")

            with score_col5:
                st.metric("Литература", f"{literature_score}/20")

                st.metric(
                    "Общий вердикт",
                    verdict
                )


            # =====================
            # СВОДКА ПО РАЗДЕЛАМ
            # =====================

            st.subheader("📋 Сводка по всем проверкам")

            tabs = st.tabs([
                "📑 ГОСТ",
                "📋 Структура",
                "📝 Введение",
                "📖 Заключение",
                "📚 Литература"
            ])


            with tabs[0]:
                st.markdown("**Оформление по ГОСТ**")

                if gost_result["font"]["status"] is None:
                    st.info(gost_result["pdf_notice"])

                else:
                    checks = {
                        "Шрифт": gost_result["font"]["status"],
                        "Размер шрифта": gost_result["size"]["status"],
                        "Межстрочный интервал": gost_result["spacing"]["status"],
                        "Выравнивание": gost_result["alignment"]["status"],
                        "Красная строка": gost_result["indent"]["status"],
                        "Заголовки": gost_result["headings"]["status"]
                    }

                    for name, status in checks.items():
                        if status:
                            st.success(f"✅ {name}: соответствует")
                        else:
                            st.error(f"❌ {name}: есть нарушения")

                    if not gost_result["headings"].get("status"):
                        for err in gost_result["headings"].get("errors", []):
                            st.error(err)
      
            with tabs[1]:
                st.markdown("**Структура работы**")

                if structure_result and "results" in structure_result:
                    for section, found in structure_result["results"].items():
                        if found:
                            st.success(f"✅ {section}: найдено")
                        else:
                            st.error(f"❌ {section}: не найдено")

                st.markdown("**Комментарий нейросети по структуре**")

                for block in split_llm_blocks(structure_llm):
                    show_colored_block(block)


            with tabs[2]:
                st.markdown("**Анализ введения**")

                for block in split_llm_blocks(intro_llm):
                    show_colored_block(block)


            with tabs[3]:
                st.markdown("**Анализ заключения**")

                for block in split_llm_blocks(conclusion_llm):
                    show_colored_block(block)


            with tabs[4]:
                st.markdown("**Анализ списка литературы**")
            
                st.info(
                    f"Найдено источников: {literature_stats['sources_count']} | "
                    f"Самый старый год: {literature_stats['oldest_year']} | "
                    f"Самый новый год: {literature_stats['latest_year']} | "
                    f"Интернет-источников: {literature_stats['internet_sources_count']}"
                )

                for block in split_llm_blocks(literature_llm):
                    show_colored_block(block)

# =====================
# ГЕНЕРАЦИЯ PDF-ОТЧЁТА
# =====================

if st.button("📄 Сгенерировать и скачать PDF-отчёт", type="primary", use_container_width=True):

    if uploaded_file is None:
        st.error("Сначала загрузите файл и выполните Полный анализ!")

    elif not st.session_state.get("analysis_done"):
        st.error("Сначала выполните Полный анализ работы!")

    else:
        gost_result = st.session_state["gost_result"]
        structure_result = st.session_state["structure_result"]
        intro_llm = st.session_state["intro_llm"]
        conclusion_llm = st.session_state["conclusion_llm"]
        literature_llm = st.session_state["literature_llm"]
        structure_llm = st.session_state["structure_llm"]
        gost_ok = st.session_state["gost_ok"]
        structure_ok = st.session_state["structure_ok"]
        total_score = st.session_state["total_score"]
        verdict = st.session_state["verdict"]
        gost_score = st.session_state["gost_score"]
        structure_score = st.session_state["structure_score"]
        intro_score = st.session_state["intro_score"]
        conclusion_score = st.session_state["conclusion_score"]
        literature_score = st.session_state["literature_score"]
        literature_stats = st.session_state["literature_stats"]
        with st.spinner("Генерируется PDF-отчёт..."):

            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.pdfbase import pdfmetrics
                from reportlab.pdfbase.ttfonts import TTFont
                from reportlab.lib.enums import TA_CENTER
                import datetime
                import os
                import re

                font_path = "C:/Windows/Fonts/arial.ttf"
                bold_font_path = "C:/Windows/Fonts/arialbd.ttf"

                pdfmetrics.registerFont(TTFont("Arial", font_path))
                pdfmetrics.registerFont(TTFont("Arial-Bold", bold_font_path))

                pdf_filename = (
                    f"Отчёт_проверки_"
                    f"{student_name.split()[0] if student_name else 'Студент'}_"
                    f"{datetime.datetime.now().strftime('%d%m%Y_%H%M')}.pdf"
                )

                doc = SimpleDocTemplate(
                    pdf_filename,
                    pagesize=A4,
                    rightMargin=50,
                    leftMargin=50,
                    topMargin=50,
                    bottomMargin=50
                )

                styles = getSampleStyleSheet()

                styles.add(ParagraphStyle(
                    name="TitleRu",
                    fontName="Arial-Bold",
                    fontSize=16,
                    leading=20,
                    alignment=TA_CENTER,
                    spaceAfter=16
                ))

                styles.add(ParagraphStyle(
                    name="HeaderRu",
                    fontName="Arial-Bold",
                    fontSize=13,
                    leading=16,
                    spaceBefore=14,
                    spaceAfter=8
                ))

                styles.add(ParagraphStyle(
                    name="TextRu",
                    fontName="Arial",
                    fontSize=10,
                    leading=14,
                    spaceAfter=6
                ))

                styles.add(ParagraphStyle(
                    name="SmallRu",
                    fontName="Arial",
                    fontSize=9,
                    leading=12,
                    spaceAfter=4
                ))

                story = []

                def clean_text(value):
                    if value is None:
                        return ""

                    value = str(value)

                    value = value.replace("&", "&amp;")
                    value = value.replace("<", "&lt;")
                    value = value.replace(">", "&gt;")
                    value = value.replace("\n", "<br/>")

                    return value

                def add_header(text):
                    story.append(Paragraph(clean_text(text), styles["HeaderRu"]))

                def add_text(text):
                    story.append(Paragraph(clean_text(text), styles["TextRu"]))

                def add_small(text):
                    story.append(Paragraph(clean_text(text), styles["SmallRu"]))

                def status_text(status):
                    if status is True:
                        return "соответствует"
                    if status is False:
                        return "есть нарушения"
                    return "не проверялось"

                # =====================
                # ТИТУЛ
                # =====================

                story.append(Paragraph("Аналитическая нейросеть МИРЭА", styles["TitleRu"]))
                story.append(Paragraph("Отчёт по проверке студенческой работы", styles["TitleRu"]))
                story.append(Spacer(1, 16))

                add_text(f"Студент: {student_name or 'Не указано'}")
                add_text(f"Группа: {group or 'Не указана'}")
                add_text(f"Направление: {selected_direction}")
                add_text(f"Тип работы: {work_type}")
                add_text(f"Тема: {topic or 'Не указана'}")
                add_text(f"Файл: {uploaded_file.name}")
                add_text(f"Дата: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")

                story.append(Spacer(1, 12))

                # =====================
                # ИТОГ
                # =====================

                add_header("Итоговый вердикт")
                add_text(f"Итоговый балл: {total_score}/100")
                add_text(f"Вердикт: {verdict}")
                add_text("Детализация баллов:")
                score_table = Table([
                    ["Критерий", "Балл"],
                    ["ГОСТ", f"{gost_score}/20"],
                    ["Структура", f"{structure_score}/20"],
                    ["Введение", f"{intro_score}/20"],
                    ["Заключение", f"{conclusion_score}/20"],
                    ["Литература", f"{literature_score}/20"],
                    ["Итого", f"{total_score}/100"]
                ])

                score_table.setStyle(TableStyle([
                    ("FONTNAME", (0, 0), (-1, -1), "Arial"),
                    ("FONTNAME", (0, 0), (-1, 0), "Arial-Bold"),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]))

                story.append(score_table)
                story.append(Spacer(1, 12))
               
                if uploaded_file.name.lower().endswith(".pdf"):
                    add_text("PDF-файл проверен по текстовым критериям. ГОСТ-оформление PDF не проверялось.")
                else:
                    add_text(f"Оформление по ГОСТ: {status_text(gost_ok)}")

                add_text(f"Структура работы: {'соответствует' if structure_ok else 'есть замечания'}")

                # =====================
                # ГОСТ
                # =====================

                add_header("1. Проверка ГОСТ")

                if gost_result["font"]["status"] is None:
                    add_text(gost_result["pdf_notice"])

                else:
                    gost_checks = {
                        "Шрифт": gost_result["font"]["status"],
                        "Размер шрифта": gost_result["size"]["status"],
                        "Межстрочный интервал": gost_result["spacing"]["status"],
                        "Выравнивание текста": gost_result["alignment"]["status"],
                        "Красная строка": gost_result["indent"]["status"],
                        "Заголовки": gost_result["headings"]["status"],
                        "Таблицы": gost_result["tables"]["status"],
                        "Рисунки": gost_result["figures"]["status"]
                    }

                    for name, status in gost_checks.items():
                        mark = "✓" if status else "✗"
                        add_text(f"{mark} {name}: {status_text(status)}")

                    heading_errors = gost_result["headings"].get("errors", [])

                    if heading_errors:
                        add_small("Замечания по заголовкам:")

                        for err in heading_errors:
                            add_small(f"- {err}")
                    table_errors = gost_result["tables"].get("errors", [])

                    if table_errors:
                        add_small("Замечания по таблицам:")

                        for err in table_errors:
                            add_small(f"- {err}")

                    figure_errors = gost_result["figures"].get("errors", [])

                    if figure_errors:
                        add_small("Замечания по рисункам:")

                        for err in figure_errors:
                            add_small(f"- {err}")

                # =====================
                # СТРУКТУРА
                # =====================

                add_header("2. Структура работы")

                if structure_result and "results" in structure_result:
                    for section, found in structure_result["results"].items():
                        mark = "✓" if found else "✗"
                        add_text(f"{mark} {section}: {'найдено' if found else 'не найдено'}")

                add_header("Комментарий по структуре")
                add_text(structure_llm)

                # =====================
                # ВВЕДЕНИЕ
                # =====================

                add_header("3. Анализ введения")
                add_text(intro_llm)

                # =====================
                # ЗАКЛЮЧЕНИЕ
                # =====================

                add_header("4. Анализ заключения")
                add_text(conclusion_llm)

                # =====================
                # ЛИТЕРАТУРА
                # =====================

                add_header("5. Анализ списка литературы")
                add_text(f"Количество источников: {literature_stats['sources_count']}")
                add_text(f"Самый старый год: {literature_stats['oldest_year']}")
                add_text(f"Самый новый год: {literature_stats['latest_year']}")
                add_text(f"Количество интернет-источников: {literature_stats['internet_sources_count']}")
                add_text(literature_llm)

                story.append(Spacer(1, 20))
                add_small("Отчёт сформирован автоматически.")

                doc.build(story)

                with open(pdf_filename, "rb") as f:
                    pdf_bytes = f.read()

                st.success("✅ PDF-отчёт успешно создан!")

                st.download_button(
                    label="⬇️ Скачать PDF-отчёт",
                    data=pdf_bytes,
                    file_name=pdf_filename,
                    mime="application/pdf"
                )

            except Exception as e:
                st.error(f"Ошибка при создании PDF: {str(e)}")