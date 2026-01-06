import re
import sys


# Mock helper
def parse_metadata_from_title(title_str: str) -> dict:
    if not title_str:
        return {"series": "", "volume": "", "clean_title": "", "tags": []}

    tags = re.findall(r"\[(.*?)\]", title_str)
    clean = re.sub(r"\[.*?\]", "", title_str).strip()

    # Clean decorative
    clean = re.sub(r"^[^\w\(\)]+", "", clean).strip()

    vol_pattern = r"(?:Volumen|Vol\.?|Tomo|v)\s*(\d+(?:\.\d+)?)"
    match = re.search(vol_pattern, clean, re.IGNORECASE)

    volume = ""
    series = clean

    if match:
        volume = match.group(1)
        full_vol_str = match.group(0)
        series = clean.replace(full_vol_str, "")

    series = re.sub(r"[\-:\s]+$", "", series).strip()
    if not series and not volume:
        series = clean

    return {"series": series, "volume": volume, "clean_title": clean, "tags": tags}


def check_redundancy(feed_title, book_title):
    print(f"--- Checking ---")
    print(f"Feed Title: '{feed_title}'")
    print(f"Book Title: '{book_title}'")

    meta_context = parse_metadata_from_title(feed_title)
    context_series = meta_context.get("series", "").lower()
    print(f"Context Series (parsed): '{meta_context.get('series')}'")

    meta = parse_metadata_from_title(book_title)
    book_series = meta["series"].lower()
    print(f"Book Series (parsed): '{meta.get('series')}'")
    print(f"Book Volume: '{meta.get('volume')}'")

    is_redundant = False
    if context_series and book_series:
        # Standard alphanumeric check
        s1 = re.sub(r"[^\w]", "", context_series)
        s2 = re.sub(r"[^\w]", "", book_series)
        print(f"s1 (clean context): '{s1}'")
        print(f"s2 (clean book): '{s2}'")

        if s1 in s2 or s2 in s1:
            is_redundant = True
            print("MATCH: Redundant!")
        else:
            print("NO MATCH.")

    return is_redundant


# Test Cases
t1_feed = "Arifureta: From Commonplace to World's Strongest [NL]"
t1_book = "Arifureta: From Commonplace to World's Strongest [NL] - Volumen 01 [TFP]"

# Note: The 'O' symbol is unicode \u2b58 or similar.
t2_feed = "Argonaut. Is It Wrong to Try to Pick Up Girls in a Dungeon? Heroic Saga [NL] - Storyline"
t2_book = "⭘ Argonaut. Is It Wrong to Try to Pick Up Girls in a Dungeon? Heroic Saga [NL] - Argonauta. Dungeon ni Deai wo Motomeru no wa Machigatteiru Darou ka? Heroic Saga - Volumen 01 [TurretT]"

check_redundancy(t1_feed, t1_book)
check_redundancy(t2_feed, t2_book)
