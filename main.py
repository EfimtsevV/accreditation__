import requests
from bs4 import BeautifulSoup
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import pdfplumber
from io import BytesIO
import re
from src.match_spec import find_matching_specialties


def extract_briefing_from_pdf(pdf_url):
    try:
        response = requests.get(pdf_url)
        pdf_file = BytesIO(response.content)

        briefing_text = ""
        with pdfplumber.open(pdf_file) as pdf:
            full_text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

            start_phrase = "Информация (брифинг) для аккредитуемого"
            end_phrase = "Действия членов АПК, вспомогательного"
            # print(full_text)
            start_index = full_text.find(start_phrase, full_text.find('Общие положения') + 1)
            end_index = full_text.find(end_phrase, full_text.find('Общие положения') + 1) - 3
            print(start_index, end_index)
            if start_index != -1 and end_index != -1 and start_index < end_index:
                raw_text = full_text[start_index + len(start_phrase): end_index].strip()
                print(raw_text)
                lines = raw_text.split('\n')
                content_lines = []

                # print(lines)

                for line in lines:
                    line = line.strip()
                    if line and len(line) > 3:
                        # print(line)
                        if not re.match(r'^\d+(\.\d+)*\s*$', line):
                            if not (line.isupper() and len(line.split()) <= 10):
                                if not re.match(r'^\d+\.\s*[А-ЯЁ]', line):
                                    if not re.match(r'^[IVX]+\.\s*[А-ЯЁ]', line):
                                        if '........' not in line and '......' not in line:
                                            if 'Стр.' not in line and 'akkredcentrmgmu' not in line:
                                                content_lines.append(line)

                briefing_text = '\n'.join(content_lines).strip()

        return briefing_text
    except Exception as e:
        print(f"Ошибка при обработке PDF {pdf_url}: {e}")
        return ""


def get_pdf_links_from_specialization(spec_url):
    session = requests.Session()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Accept': 'text/html, */*; q=0.01',
        'Sec-Fetch-Site': 'same-origin',
        'Accept-Language': 'ru',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Fetch-Mode': 'cors',
        'Origin': 'https://fmza.ru',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15',
        'Referer': spec_url.rstrip('/') + '/',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'empty',
        'X-Requested-With': 'XMLHttpRequest',
        'Priority': 'u=3, i'
    }

    try:
        initial_response = session.get(spec_url)

        post_url = spec_url.rstrip('/') + '/index.php'
        data = 'ID_MENU=LIST_SKILL'

        response = session.post(post_url, data=data, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        pdf_links = set()

        all_links = soup.find_all('a', href=True)

        for link in all_links:
            link_text = link.get_text(strip=True).lower()
            href = link['href']

            if "паспорт станции" in link_text:
                full_url = urllib.parse.urljoin('https://fmza.ru/', href)

                if href.endswith('.pdf'):
                    pdf_links.add(full_url)
                elif not href.endswith('.pdf') and href != '#':
                    try:
                        html_response = session.get(full_url)
                        html_soup = BeautifulSoup(html_response.text, 'html.parser')
                        html_links = html_soup.find_all('a', href=True)

                        for html_link in html_links:
                            html_href = html_link['href']
                            html_link_text = html_link.get_text(strip=True).lower()
                            if html_href.endswith('.pdf') and "паспорт станции" in html_link_text:
                                pdf_full_url = urllib.parse.urljoin(full_url, html_href)
                                pdf_links.add(pdf_full_url)
                    except:
                        continue

        return list(pdf_links)
    except Exception as e:
        print(f"Ошибка при обработке специализации {spec_url}: {e}")
        return []


def process_specialization(spec):
    print(f"Обрабатываю специализацию: {spec['fmza_name']}")
    pdf_links = get_pdf_links_from_specialization(spec['fmza_url'])

    briefings = []
    for pdf_url in pdf_links:
        print(f"Извлекаю брифинг из: {pdf_url}")
        briefing_text = extract_briefing_from_pdf(pdf_url)
        print(briefing_text)
        if briefing_text and len(briefing_text.strip()) > 50:
            briefings.append(briefing_text)

    return {
        'name': spec['fmza_name'],
        'url': spec['fmza_url'],
        'pdf_links': pdf_links,
        'briefings': briefings
    }


def main():
    print("Получаю список специализаций...")
    specs = find_matching_specialties()
    print(f"Найдено {len(specs)} совпадающих специализаций")

    result = []
    print("Начинаю обработку специализаций...")

    with ThreadPoolExecutor(max_workers=50) as executor:
        future_to_spec = {executor.submit(process_specialization, spec): spec for spec in specs}
        for future in as_completed(future_to_spec):
            try:
                result.append(future.result())
            except Exception as e:
                print(f"Ошибка при обработке: {e}")

    print("Создаю Excel файл...")

    specializations_data = []
    briefings_data = []
    relations_data = []

    spec_id = 1
    briefing_id = 1

    for spec_result in result:
        specializations_data.append({
            'ID специализации': spec_id,
            'Название специализации': spec_result['name']
        })

        for briefing in spec_result['briefings']:
            briefings_data.append({
                'ID брифинга': briefing_id,
                'Текст брифинга': briefing
            })

            relations_data.append({
                'ID специализации': spec_id,
                'ID брифинга': briefing_id
            })

            briefing_id += 1

        spec_id += 1

    df_specializations = pd.DataFrame(specializations_data)
    df_briefings = pd.DataFrame(briefings_data)
    df_relations = pd.DataFrame(relations_data)

    with pd.ExcelWriter('result.xlsx', engine='openpyxl') as writer:
        df_specializations.to_excel(writer, sheet_name='Специализации', index=False)
        df_briefings.to_excel(writer, sheet_name='Брифинги', index=False)
        df_relations.to_excel(writer, sheet_name='Связи', index=False)

    print(f"Excel файл создан: result.xlsx")
    print(f"Обработано специализаций: {len(specializations_data)}")
    print(f"Извлечено брифингов: {len(briefings_data)}")
    print(f"Создано связей: {len(relations_data)}")

    for spec_result in result:
        print(f"\nСпециализация: {spec_result['name']}")
        print(f"PDF файлов найдено: {len(spec_result['pdf_links'])}")
        print(f"Брифингов извлечено: {len(spec_result['briefings'])}")


if __name__ == "__main__":
    main()