import re


def find_section(text, patterns):

    text_lower = text.lower()

    text_lower = re.sub(
        r"\s+",
        " ",
        text_lower
    )

    for pattern in patterns:

        if re.search(
            pattern,
            text_lower,
            re.IGNORECASE
        ):
            return True

    return False


def check_structure(text):

    sections = {

        "Титульный лист": [
            r"министерство",
            r"рт[уы]\s*мирэа",
            r"институт"
        ],

        "Содержание": [
            r"\bсодержание\b",
            r"\bоглавление\b",
            r"с\s*о\s*д\s*е\s*р\s*ж\s*а\s*н\s*и\s*е",
            r"о\s*г\s*л\s*а\s*в\s*л\s*е\s*н\s*и\s*е"
        ],

        "Введение": [
            r"\bвведение\b"
        ],

        "Глава 1": [
            r"глава\s*1",
            r"1\.\s",
            r"1\.1"
        ],

        "Глава 2": [
            r"глава\s*2",
            r"2\.\s",
            r"2\.1"
        ],

        "Заключение": [
            r"\bзаключение\b",
            r"\bвыводы\b"
        ],

        "Список источников": [
            r"список использованных источников",
            r"список литературы",
            r"библиографический список"
        ],

        "Приложения": [
            r"\bприложение\b",
            r"\bприложения\b"
        ]
    }

    results = {}

    for section_name, patterns in sections.items():

        results[section_name] = find_section(
            text,
            patterns
        )

    missing = []

    for section, exists in results.items():

        if not exists:

            missing.append(section)

    return {
        "results": results,
        "missing": missing
    }

def extract_document_headings(text):

    if not text:
        return ""

    headings = []

    lines = text.splitlines()

    heading_patterns = [
        r"^содержание$",
        r"^оглавление$",
        r"^введение$",
        r"^заключение$",
        r"^список использованных источников$",
        r"^список литературы$",
        r"^библиографический список$",
        r"^приложения?$",
        r"^глава\s+\d+",
        r"^\d+\.\s+",
        r"^\d+\.\d+\s+"
    ]

    for line in lines:

        clean = line.strip()

        if not clean:
            continue

        lower = clean.lower()

        if len(clean) > 120:
            continue

        for pattern in heading_patterns:
            if re.match(pattern, lower):
                headings.append(clean)
                break

    return "\n".join(headings)