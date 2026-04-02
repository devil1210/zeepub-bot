import os
import random

from dotenv import load_dotenv
from supabase import create_client


def generate_premium_themes(count: int = 100) -> list[dict]:
    # Expanded palettes specifically for requested themes
    palettes = [
        # --- PASTEL THEMES ---
        ("#FFADAD", "#FFF5F5", "#FFFFFF", "Soft Strawberry"),
        ("#FFD6A5", "#FFFBF5", "#FFFFFF", "Peach Fuzz"),
        ("#FDFFB6", "#FFFFF5", "#FFFFFF", "Lemon Chiffon"),
        ("#CAFFBF", "#F5FFF5", "#FFFFFF", "Mint Cream"),
        ("#9BF6FF", "#F5FFFF", "#FFFFFF", "Sky Blue Pastel"),
        ("#A0C4FF", "#F5F8FF", "#FFFFFF", "Periwinkle Dream"),
        ("#BDB2FF", "#F8F5FF", "#FFFFFF", "Lavender Whip"),
        ("#FFC6FF", "#FFF5FF", "#FFFFFF", "Bubblegum"),
        ("#FFB7B2", "#FFF2F1", "#FFFFFF", "Rose Water"),
        ("#B2F7EF", "#F0FFFF", "#FFFFFF", "Electric Mint"),
        # --- ANIME THEMES ---
        ("#FF69B4", "#FFF0F5", "#FFFFFF", "Sakura Blossom (Anime)"),
        ("#00BFFF", "#1A1A2E", "#16213E", "Mecha Core (Anime)"),
        ("#FFD700", "#2C003E", "#510A32", "Magical Moon (Anime)"),
        ("#FF4500", "#121212", "#1F1F1F", "Shinobi Path (Anime)"),
        ("#7C0000", "#000000", "#1A1A1A", "Cursed Spirit (Anime)"),
        ("#E6E6FA", "#2E004B", "#4A0072", "ASTRAL Chain (Anime)"),
        ("#00FF41", "#0D0208", "#003B00", "Digital World (Anime)"),
        ("#FFD1DC", "#4B0082", "#2D004B", "Neo Tokyo Night"),
        ("#66FCF1", "#1F2833", "#0B0C10", "Ghost in Shell"),
        ("#F13C20", "#4056A1", "#D79922", "Studio Ghibi Sky"),
        # --- RETRO / VINTAGE THEMES ---
        ("#FF00FF", "#000000", "#111111", "Vaporwave Neon"),
        ("#00FFFF", "#120458", "#240b36", "Synthwave Sky"),
        ("#9BBC0F", "#8BAC0F", "#306230", "Classic DMG (Retro)"),
        ("#F83800", "#000000", "#2038EC", "NES Original"),
        ("#FFCC00", "#333333", "#000000", "8-Bit Sunset"),
        ("#39FF14", "#000000", "#050505", "CRT Terminal"),
        ("#FF61D2", "#1E1E2E", "#313244", "Retrofuturism"),
        ("#FFE4B5", "#8B4513", "#A0522D", "Analog Tape"),
        ("#E2D1F9", "#317773", "#FFFFFF", "90s Browser"),
        ("#00FF00", "#000000", "#001100", "Fallout Terminal (Retro)"),
        # --- GAME INSPIRED ---
        ("#E50000", "#121212", "#1E1E1E", "Persona Crimson"),
        ("#B68D40", "#122620", "#D6AD60", "Hyrule Legend"),
        ("#00CCFF", "#001B3D", "#002B5B", "Vault Dweller"),
        ("#A4A4A4", "#2E2428", "#5D4E60", "Shadow Moses"),
        ("#9146FF", "#0B0E11", "#18181B", "Streamer Pulse"),
        ("#FF9900", "#202020", "#282828", "Overwatch Gold"),
        ("#FF0000", "#FFFFFF", "#F0F0F0", "Mario World"),
        ("#4E9AF1", "#000000", "#121212", "Mass Effect Blue"),
        ("#C0C0C0", "#2D2D2D", "#1A1A1A", "Dark Souls Embers"),
        ("#3D9970", "#1B1B1B", "#2B2B2B", "Spartan Green"),
        # --- NATURE / SEASONS ---
        ("#FF7F50", "#FFF5EE", "#FFFFFF", "Coral Reef"),
        ("#20B2AA", "#E0FFFF", "#FFFFFF", "Arctic Ice"),
        ("#8B4513", "#FFF8DC", "#FFFFFF", "Autumn Maple"),
        ("#006400", "#F5FFFA", "#FFFFFF", "Forest Moss"),
        ("#4682B4", "#F0F8FF", "#FFFFFF", "Soft Rain"),
        ("#DAA520", "#FFFACD", "#FFFFFF", "Golden Hour"),
        ("#483D8B", "#191970", "#000080", "Starlight Night"),
        ("#BC8F8F", "#FFF0F5", "#FFFFFF", "Dusty Rose"),
        ("#556B2F", "#F5F5DC", "#FFFFFF", "Olive Grove"),
        ("#008080", "#E0F2F1", "#FFFFFF", "Deep Teal"),
        # --- MODERN / TECH ---
        ("#3B82F6", "#0F172A", "#1E293B", "Tailwind Dark"),
        ("#6366F1", "#FFFFFF", "#F8FAFC", "Indigo Modern"),
        ("#EC4899", "#111827", "#1F2937", "Pink Cyber"),
        ("#06B6D4", "#083344", "#164E63", "Turquoise Tech"),
        ("#F59E0B", "#1E1B4B", "#312E81", "Amber Indigo"),
        ("#10B981", "#064E3B", "#065F46", "Emerald Night"),
        ("#8B5CF6", "#1E1631", "#2D214F", "Ultra Violet"),
        ("#F43F5E", "#180D0E", "#2A1214", "Deep Crimson"),
        ("#14B8A6", "#042F2E", "#0F766E", "Teal Abyss"),
        ("#0ea5e9", "#0c0a09", "#1c1917", "Onyx Blue"),
        # --- EXTRA / CREATIVE ---
        ("#FFBF00", "#1A1A1A", "#262626", "Bumblebee"),
        ("#FF4E50", "#F9D423", "#FFFFFF", "Sunrise Mix"),
        ("#ED4264", "#FFEDBC", "#FFFFFF", "Strawberry Cream"),
        ("#27ae60", "#2c3e50", "#34495e", "Peter River Green"),
        ("#8e44ad", "#2c3e50", "#34495e", "Amethyst Night"),
        ("#e67e22", "#d35400", "#e67e22", "Pumpkin Spice"),
        ("#bdc3c7", "#2c3e50", "#95a5a6", "Silver Cloud"),
        ("#7f8c8d", "#1a1a1a", "#2c3e50", "Flat UI Heavy"),
        ("#1abc9c", "#2ecc71", "#16a085", "Emerald Flat"),
        ("#3498db", "#2980b9", "#34495e", "Belize Hole"),
        # --- AMOLED VARIATIONS ---
        ("#00FF00", "#000000", "#050505", "Toxic (AMOLED)"),
        ("#FF0000", "#000000", "#080000", "Bloodline (AMOLED)"),
        ("#00BFFF", "#000000", "#000810", "Deep Sea (AMOLED)"),
        ("#FFD700", "#000000", "#0A0A00", "Golden Sovereign (AMOLED)"),
        ("#FFFFFF", "#000000", "#0F0F0F", "Void White (AMOLED)"),
        ("#FF00FF", "#000000", "#100010", "Electric Purple (AMOLED)"),
        ("#00FFFF", "#000000", "#001010", "Liquid Cyan (AMOLED)"),
        ("#FF4500", "#000000", "#100500", "Obsidian Sun (AMOLED)"),
        ("#C0C0C0", "#000000", "#0C0C0C", "Platinum (AMOLED)"),
        ("#7B68EE", "#000000", "#050010", "Medusa (AMOLED)"),
        # --- RANDOM MIXES (Filling to 100) ---
        ("#E91E63", "#FCE4EC", "#FFFFFF", "Candy Pink"),
        ("#9C27B0", "#F3E5F5", "#FFFFFF", "Royal Lavender"),
        ("#673AB7", "#EDE7F6", "#FFFFFF", "Deep Indigo"),
        ("#3F51B5", "#E8EAF6", "#FFFFFF", "Navy Blue Light"),
        ("#2196F3", "#E3F2FD", "#FFFFFF", "Sky Blue Day"),
        ("#03A9F4", "#E1F5FE", "#FFFFFF", "Light Blue Breeze"),
        ("#00BCD4", "#E0F7FA", "#FFFFFF", "Cyan Fresh"),
        ("#009688", "#E0F2F1", "#FFFFFF", "Pale Teal"),
        ("#4CAF50", "#E8F5E9", "#FFFFFF", "Garden Green"),
        ("#8BC34A", "#F1F8E9", "#FFFFFF", "Lime Light"),
        ("#CDDC39", "#F9FBE7", "#FFFFFF", "Pear Green"),
        ("#FFEB3B", "#FFFDE7", "#FFFFFF", "Yellow Sunny"),
        ("#FFC107", "#FFF8E1", "#FFFFFF", "Amber Warm"),
        ("#FF9800", "#FFF3E0", "#FFFFFF", "Orange Crush"),
        ("#FF5722", "#FBEBE9", "#FFFFFF", "Deep Orange"),
        ("#795548", "#EFEBE9", "#FFFFFF", "Coffee Brown"),
        ("#9E9E9E", "#F5F5F5", "#FFFFFF", "Grey Neutral"),
        ("#607D8B", "#ECEFF1", "#FFFFFF", "Blue Grey Modern"),
        ("#000000", "#FFFFFF", "#F9F9F9", "High Contrast Light"),
        ("#FFFFFF", "#121212", "#1E1E1E", "Inverted Dark"),
    ]

    themes = []

    for i in range(count):
        # Pick palette (cycle if count > palettes)
        p_idx = i % len(palettes)
        primary, bg, card, name = palettes[p_idx]

        # Determine theme_type
        if "(AMOLED)" in name:
            theme_type = "amoled"
        elif "#f" in bg.lower() and bg.lower() not in ["#ff0000", "#e50000"]:
            theme_type = "light"
        else:
            theme_type = "dark"

        # Unique naming
        v_name = f"{name} {(i // len(palettes)) + 1}" if i >= len(palettes) else name

        # Generation with high variation for uniqueness
        themes.append(
            {
                "name": v_name,
                "description": f"Colección Premium: Tema {v_name} ({theme_type}). Especialmente diseñado para una experiencia visual inmersiva.",
                "theme_type": theme_type,
                "primary_color": primary,
                "background_color": bg,
                "card_color": card,
                "glass_blur": random.choice([4, 8, 12, 16, 20, 24, 30]),
                "glass_opacity": round(random.uniform(0.3, 0.85), 2),
                "nav_opacity": round(random.uniform(0.6, 0.98), 2),
                "accent_opacity": round(random.uniform(0.05, 0.35), 2),
                "card_glow_intensity": round(random.uniform(0.2, 0.9), 2),
                "font_size": random.choice([13, 14, 15, 16]),
                "cover_width": random.choice([100, 110, 120, 130]),
            }
        )

    return themes


if __name__ == "__main__":
    load_dotenv()

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        print("Error: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        exit(1)

    supabase = create_client(url, key)

    # Generate 100 NEW unique themes
    new_themes = generate_premium_themes(100)

    print("🚀 Generando e insertando 100 nuevos temas premium...")

    try:
        # Upsert allows updating if names collide or just adding new ones
        res = supabase.table("app_themes").upsert(new_themes).execute()
        print("✅ ¡Éxito! Se han añadido/actualizado 100 temas en la base de datos.")
        print(f"Total de registros procesados: {len(res.data)}")
    except Exception as e:
        print(f"❌ Error al insertar temas: {e}")
