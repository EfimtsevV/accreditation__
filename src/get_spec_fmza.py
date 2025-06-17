import requests
from bs4 import BeautifulSoup
import urllib.parse

import warnings

warnings.filterwarnings("ignore", message=".*CropBox.*")
def scrape_specializations():
    base_url = "https://fmza.ru/fos_primary_specialized/"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    spec_links = soup.find_all('a', href=True)

    specializations = []
    for link in spec_links:
        if 'fos_primary_specialized' in link['href'].lower():
            specializations.append({
                'name': link.text.strip(),
                'url': urllib.parse.urljoin(base_url, link['href'])
            })
    print(specializations)
    return specializations


all_specialties = (scrape_specializations())[1:]
only_names_all_specialties = [spec['name'] for spec in all_specialties]

# print(f"Извлечено {len(only_names_all_specialties)} специальностей:")
# for i, name in enumerate(only_names_all_specialties, 1):
#     print(f"{i}. {name}")