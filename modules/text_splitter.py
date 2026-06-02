import re


def extract_intro(text):

    if not text:
        return None

    text_lower = text.lower()

    matches = list(
        re.finditer(r"\bвведение\b", text_lower)
    )

    if not matches:
        return None

    # Берём последнее вхождение "Введение",
    # чтобы пропустить содержание
    start_index = matches[-1].start()

    end_patterns = [
        r"\n\s*1\.\s*",
        r"\n\s*1\.1\s*",
        r"\bглава\s*1\b",
        r"\bанализ\s+текущего\s+процесса",
        r"\bтеоретичес"
    ]

    end_index = len(text)

    search_area = text[start_index + 20:]

    for pattern in end_patterns:
        match = re.search(
            pattern,
            search_area,
            flags=re.IGNORECASE
        )

        if match:
            possible_end = start_index + 20 + match.start()

            if possible_end < end_index:
                end_index = possible_end

    intro_text = text[start_index:end_index].strip()

    if len(intro_text) < 80:
        return None

    return intro_text