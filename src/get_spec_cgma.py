import pdfplumber
import requests
from io import BytesIO
import warnings

warnings.filterwarnings("ignore", message=".*CropBox.*")

def extract_specialties_from_pdf(pdf_url):
    # Скачиваем PDF файл
    response = requests.get(pdf_url)
    pdf_file = BytesIO(response.content)

    specialties = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            # Извлекаем таблицу со страницы
            table = page.extract_table()

            if not table:
                continue

            # Проверяем заголовки таблицы (первая строка)
            headers = table[0]
            column_index = 1

            for row in table:
                if len(row) > column_index and row[column_index]:
                    specialty = row[column_index].strip()
                    if specialty:
                        specialties.append(specialty)

    return specialties[1:]

pdf_url_cgma = "https://cgma.su/center/akkreditatsiya/График_ПСАС_июнь-июль_%202025.pdf"

cgma_specialties = extract_specialties_from_pdf(pdf_url_cgma)
