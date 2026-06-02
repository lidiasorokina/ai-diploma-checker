import re


def extract_literature(text):

    if not text:
        return ""

    text_lower = text.lower()

    start_patterns = [
        r"список\s+использованных\s+источников",
        r"список\s+литературы",
        r"библиографический\s+список",
        r"источники"
    ]

    matches = []

    for pattern in start_patterns:
        for match in re.finditer(pattern, text_lower):
            matches.append(match)

    if not matches:
        return ""

    # Берём последнее вхождение, чтобы не взять пункт из содержания
    start_index = max(
        match.start()
        for match in matches
    )

    end_patterns = [
        r"\bприложение\b",
        r"\bприложения\b",
        r"\bappendix\b"
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

    literature_text = text[start_index:end_index].strip()

    # Убираем сам заголовок
    literature_text = re.sub(
        r"^(список\s+использованных\s+источников|список\s+литературы|библиографический\s+список|источники)",
        "",
        literature_text,
        flags=re.IGNORECASE
    ).strip()

    return literature_text


def split_sources(literature_text):

    if not literature_text:
        return []

    lines = [
        line.strip()
        for line in literature_text.splitlines()
        if line.strip()
    ]

    sources = []
    current_source = ""

    source_start_patterns = [
        r"^\d+\.",
        r"^\d+\)",
        r"^\[\d+\]",
        r"^\d+\s+[А-ЯA-Z]"
    ]

    for line in lines:

        is_new_source = any(
            re.match(pattern, line)
            for pattern in source_start_patterns
        )

        if is_new_source:

            if current_source:
                sources.append(current_source.strip())

            current_source = line

        else:

            if current_source:
                current_source += " " + line

            else:
                current_source = line

    if current_source:
        sources.append(current_source.strip())

    return sources


def analyze_literature_stats(literature_text):

    sources = split_sources(literature_text)

    years = re.findall(
        r"\b(19\d{2}|20\d{2})\b",
        literature_text or ""
    )

    years = [
        int(year)
        for year in years
        if 1990 <= int(year) <= 2035
    ]

    internet_sources = []

    for source in sources:

        lower = source.lower()

        if (
            "http" in lower
            or "www." in lower
            or "doi" in lower
            or "url" in lower
            or "электрон" in lower
            or "режим доступа" in lower
        ):
            internet_sources.append(source)

    return {
        "sources_count": len(sources),
        "latest_year": max(years) if years else None,
        "oldest_year": min(years) if years else None,
        "internet_sources_count": len(internet_sources),
        "sources": sources
    }