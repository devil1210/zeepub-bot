import re

clean = "Aren’t You Too Sweet Salt-God Sato-San? ║ Sato-san, la Fría, Solo es Dulce Conmigo ║ Shiotaiou no Satou-san ga Ore ni dake Amai"

# current
parts = re.split(r"[\-\–\—\−\―\:\~～\|¦]", clean)
print("CURRENT:")
for idx, p in enumerate(parts):
    print(f"  {idx}: {p.strip()}")
    
# proposed to avoid splitting compound words like "Salt-God" or "Sato-san"
# Require spaces around dashes/tildes/pipes, but allow colon without space 
# AND ALSO explicitly match " ║ " because ║ wasn't even in the array!
parts2 = re.split(r"(?:\s+[\-\–\—\−\―\~～\|¦║]\s+)|(?:\s*:\s*)", clean)
print("PROPOSED:")
for idx, p in enumerate(parts2):
    print(f"  {idx}: {p.strip()}")
