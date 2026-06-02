import re

def extract_conclusion(text):

    if not text:
        return None

    text_lower = text.lower()

    start_matches = list(
        re.finditer(r"\bзаключение\b", text_lower)
    )

    if not start_matches:
        return None

    # Берём последнее вхождение, чтобы не взять "Заключение" из содержания
    start_index = start_matches[-1].start()

    end_patterns = [
        r"список использованных источников",
        r"список литературы",
        r"библиографический список",
        r"приложения?",
        r"references"
    ]

    end_index = len(text)

    for pattern in end_patterns:

        match = re.search(
            pattern,
            text_lower[start_index:]
        )

        if match:
            possible_end = start_index + match.start()

            if possible_end < end_index:
                end_index = possible_end

    conclusion_text = text[start_index:end_index].strip()

    if len(conclusion_text) < 50:
        return None

    return conclusion_text