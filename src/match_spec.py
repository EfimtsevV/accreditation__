import sys
from pathlib import Path
import re
import warnings

warnings.filterwarnings("ignore", message=".*CropBox.*")

sys.path.append(str(Path(__file__).parent.parent))

from src.get_spec_cgma import cgma_specialties
from src.get_spec_fmza import all_specialties


def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[-–—]', ' ', text)
    text = re.sub(r'\bи\b|\bили\b', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    words = sorted(text.strip().split())
    return ' '.join(words)


def find_matching_specialties():
    cgma_dict = {normalize_text(spec): spec for spec in cgma_specialties}
    cgma_normalized = set(cgma_dict.keys())

    matches_spec = []

    for fmza_spec in all_specialties:
        fmza_normalized = normalize_text(fmza_spec['name'])

        if fmza_normalized in cgma_normalized:
            # оригинальное название из cgma для отчета
            # matched_name = cgma_dict[fmza_normalized]
            matches_spec.append({
                'fmza_name': fmza_spec['name'],
                'fmza_url': fmza_spec['url']
            })

    return matches_spec
