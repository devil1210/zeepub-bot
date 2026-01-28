import os
import sys

# Añadir el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.helpers import parse_metadata_from_title

titles = [
    "⭘ Alya Sometimes Hides Her Feelings in Russian [NL] - Tokidoki Bosotto Russiago de Dereru Tonari no Arya-san - Volumen 01 [Vlady]",
    "⭘ 86 - EIGHTY-SIX [NL] - 86 ―Eitishikkusu― - Volumen 01 [TFP]",
    "⭘ Sword Art Online [NL] - Volumen 01",
]

for t in titles:
    res = parse_metadata_from_title(t)
    print(f"Original: {t}")
    print(f"  -> CleanTitle: {res['clean_title']}")
    print(f"  -> Romaji:     {res['romaji']}")
    print(f"  -> Vol:        {res['volume']}")
    print(f"  -> Tags:       {res['tags']}")
    print("-" * 50)
