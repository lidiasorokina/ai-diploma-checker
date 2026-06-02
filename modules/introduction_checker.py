def check_introduction(text: str):
    if not text or len(text) < 100:
        return {"Ошибка": "Текст слишком короткий или пустой"}
    
    text_lower = text.lower()
    
    # Диагностика
    has_aktualnost = "актуальность" in text_lower
    has_aktualnost_temy = "актуальность темы" in text_lower
    position = text_lower.find("актуальность")
    
    results = {
        "Актуальность": has_aktualnost,
        "Цель исследования": "цель" in text_lower and any(x in text_lower for x in ["работы", "заключается", "данной"]),
        "Задачи исследования": "задачи" in text_lower,
    }
    
    # Выводим диагностику в консоль (посмотрим в терминале)
    print("=== ДИАГНОСТИКА ВВЕДЕНИЯ ===")
    print(f"Найдено 'актуальность': {has_aktualnost}")
    print(f"Позиция в тексте: {position}")
    print(f"Длина текста: {len(text)} символов")
    print("============================")
    
    return results