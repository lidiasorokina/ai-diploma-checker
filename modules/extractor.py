from docx import Document
import pdfplumber
import io
import zipfile
import xml.etree.ElementTree as ET


def extract_text_from_docx(file):
    """Извлекает текст из DOCX файла (устойчиво к повреждениям)"""
    try:
        file.seek(0)
        doc = Document(io.BytesIO(file.read()))
        full_text = [para.text for para in doc.paragraphs if para.text.strip()]
        return "\n".join(full_text)
        
    except Exception as first_error:
        # Если обычный способ не сработал — пробуем грубое извлечение
        try:
            file.seek(0)
            bytes_data = file.read()
            
            with zipfile.ZipFile(io.BytesIO(bytes_data)) as zip_file:
                if 'word/document.xml' in zip_file.namelist():
                    with zip_file.open('word/document.xml') as xml_file:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()
                        namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                        
                        texts = []
                        for paragraph in root.findall('.//w:p', namespaces):
                            for t in paragraph.findall('.//w:t', namespaces):
                                if t.text:
                                    texts.append(t.text)
                        
                        return "\n".join(texts)
                else:
                    raise Exception("Не найден document.xml")
        except Exception as backup_error:
            raise Exception(f"Не удалось извлечь текст из DOCX. Файл может быть повреждён.\n"
                          f"Обычная ошибка: {first_error}\n"
                          f"Резервная ошибка: {backup_error}")


def extract_text_from_pdf(file):
    """Извлекает текст из PDF файла"""

    try:
        file.seek(0)

        text = []

        with pdfplumber.open(
            io.BytesIO(file.read())
        ) as pdf:

            for page_num, page in enumerate(pdf.pages):

                try:
                    page_text = page.extract_text()

                    # Если обычный extract_text не помог
                    if not page_text:

                        words = page.extract_words()

                        if words:
                            page_text = " ".join(
                                word["text"]
                                for word in words
                            )

                    if page_text and page_text.strip():

                        text.append(page_text)

                except Exception as page_error:

                    print(
                        f"Ошибка страницы "
                        f"{page_num}: {page_error}"
                    )

                    continue

        final_text = "\n".join(text)

        if not final_text.strip():

            raise Exception(
                "PDF не содержит текстового слоя"
            )

        return final_text

    except Exception as e:

        raise Exception(
            f"Ошибка при обработке PDF: {str(e)}"
        )


def extract_text(file, filename: str):
    """Главная функция"""
    try:
        file.seek(0)

        if filename.lower().endswith(".docx"):
            return extract_text_from_docx(file)

        elif filename.lower().endswith(".pdf"):
            return extract_text_from_pdf(file)

        else:
            raise Exception("Неподдерживаемый формат файла")

    except Exception as e:
        raise Exception(f"Ошибка extract_text: {str(e)}")