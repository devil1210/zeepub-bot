import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from utils.helpers import parse_metadata_from_title

test_titles = [
    "○ 5 Centimeters per Second + Children Who Chase Lost Voices [NL] - Byōsoku Go Senchimētoru + Hoshi wo Ou Kodomo no Koe [NL] - Volumen 01",
    "Arifureta: From Commonplace to World's Strongest [NL] - Arifureta Shokugyou de Sekai Saikyou - Volumen 01 [TFP]"
]

for title in test_titles:
    print(f"\nTesting: {title}")
    res = parse_metadata_from_title(title)
    print(f"  Series: {res.get('series')}")
    print(f"  Volume: {res.get('volume')}")
    print(f"  Romaji: {res.get('romaji')}")
    print(f"  Clean:  {res.get('clean_title')}")
    print(f"  Tags:   {res.get('tags')}")
