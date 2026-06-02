from docx import Document
import os
import fitz
import re


def read_pdf(path):
    text = ""

    try:
        doc = fitz.open(path)

        for page in doc:
            text += page.get_text() + "\n"

        doc.close()

    except Exception as e:
        print(f"Ошибка чтения PDF {path}: {e}")

    return text


def read_docx(path):
    text = []

    try:
        doc = Document(path)

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)

    except Exception as e:
        print(f"Ошибка чтения DOCX {path}: {e}")

    return "\n".join(text)


def read_file(path):
    filename = path.lower()

    if filename.endswith(".docx"):
        return read_docx(path)

    if filename.endswith(".pdf"):
        return read_pdf(path)

    return ""


def get_keywords(text):
    if not text:
        return set()

    text = text.lower()

    words = re.findall(r"[а-яa-z0-9]{4,}", text)

    stop_words = {
        "работа", "курсовая", "дипломная", "проект",
        "тема", "система", "анализ", "разработка",
        "исследование", "основные", "данные"
    }

    return set(word for word in words if word not in stop_words)


def score_method(filename, method_text, topic="", group="", direction=""):
    score = 0

    full = (filename + " " + method_text[:3000]).lower()

    # Нормоконтроль всегда в приоритете
    if (
        "нормоконтроль" in full
        or "нормоконтрол" in full
        or "оформлен" in full
        or "гост" in full
    ):
        score += 100

    # Совпадение направления
    if direction and direction.lower() in full:
        score += 30

    # Совпадение группы
    if group and group.lower() in full:
        score += 25

    # Совпадение темы по ключевым словам
    topic_keywords = get_keywords(topic)

    for word in topic_keywords:
        if word in full:
            score += 10

    return score


def load_method_base(
    direction="",
    topic="",
    group="",
    uploaded_method_path=None
):
    selected_texts = []
    candidates = []

    # 1. Нормоконтроль
    norm_folder = "data/methods/normcontrol"

    if os.path.exists(norm_folder):
        for filename in os.listdir(norm_folder):
            if filename.endswith((".docx", ".pdf")):
                path = os.path.join(norm_folder, filename)
                text = read_file(path)

                if text.strip():
                    candidates.append({
                        "filename": filename,
                        "path": path,
                        "text": text,
                        "priority": 1000
                    })

    # 2. Методичка, загруженная студентом
    if uploaded_method_path and os.path.exists(uploaded_method_path):
        text = read_file(uploaded_method_path)

        if text.strip():
            candidates.append({
                "filename": os.path.basename(uploaded_method_path),
                "path": uploaded_method_path,
                "text": text,
                "priority": 900
            })

    # 3. Методички направления
    direction_folder = f"data/methods/{direction}"

    direction_exists = False

    if direction and os.path.exists(direction_folder):
        files = [
            f for f in os.listdir(direction_folder)
            if f.endswith((".docx", ".pdf"))
        ]

        if files:
            direction_exists = True

        for filename in files:
            path = os.path.join(direction_folder, filename)
            text = read_file(path)

            if text.strip():
                candidates.append({
                    "filename": filename,
                    "path": path,
                    "text": text,
                    "priority": 0
                })

    # 4. Оценка релевантности
    for item in candidates:
        item["score"] = item["priority"] + score_method(
            filename=item["filename"],
            method_text=item["text"],
            topic=topic,
            group=group,
            direction=direction
        )

    candidates = sorted(
        candidates,
        key=lambda x: x["score"],
        reverse=True
    )

    # Берём максимум 3 самых подходящих файла
    selected = candidates[:3]

    for item in selected:
        selected_texts.append(
            f"\n\n===== ИСТОЧНИК МЕТОДИЧКИ: {item['filename']} =====\n"
            f"{item['text']}"
        )

    result_text = "\n".join(selected_texts)

    return result_text, direction_exists