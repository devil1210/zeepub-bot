import random
from typing import List, Dict

def generate_themes() -> List[Dict]:
    modes = ['light', 'dark', 'amoled']
    
    # Predefined color palettes (Primary, Background, Card)
    palettes = [
        # Dark/Deep
        ("#3b82f6", "#0f172a", "#1e293b", "Ocean Deep"),
        ("#10b981", "#064e3b", "#065f46", "Forest Night"),
        ("#f43f5e", "#450a0a", "#7f1d1d", "Ruby Velvet"),
        ("#8b5cf6", "#1e1b4b", "#312e81", "Midnight Purple"),
        ("#f59e0b", "#451a03", "#78350f", "Amber Glow"),
        
        # AMOLED (Pure Black Background)
        ("#00ff00", "#000000", "#0a0a0a", "Matrix (AMOLED)"),
        ("#ff00ff", "#000000", "#0f000f", "Cyber Pink (AMOLED)"),
        ("#00ffff", "#000000", "#000f0f", "Neon Ice (AMOLED)"),
        ("#ffffff", "#000000", "#111111", "Monochrome (AMOLED)"),
        ("#ff3d00", "#000000", "#120500", "Solar Flare (AMOLED)"),

        # Light 
        ("#2563eb", "#f8fafc", "#ffffff", "Classic Blue"),
        ("#db2777", "#fdf2f8", "#ffffff", "Sakura Blossom"),
        ("#059669", "#f0fdf4", "#ffffff", "Mint Fresh"),
        ("#d97706", "#fffbeb", "#ffffff", "Golden Sand"),
        ("#7c3aed", "#f5f3ff", "#ffffff", "Lavender Mist"),
        
        # Cyberpunk
        ("#00fbff", "#050608", "#0d1117", "Retro Future"),
        ("#ff00cc", "#0c0e14", "#161b22", "Night City"),
        ("#7aff00", "#0a0a0a", "#1a1a1a", "Biohazard"),
        ("#ffcc00", "#121212", "#1e1e1e", "Hacker Gold"),
        
        # Nature
        ("#2d6a4f", "#1b4332", "#2d6a4f", "Evergreen"),
        ("#76c893", "#f1f8e9", "#ffffff", "Meadow"),
        ("#bc6c25", "#fefae0", "#ffffff", "Autumn Leaf"),
        ("#606c38", "#283618", "#606c38", "Deep Forest"),
        
        # Minimal/Gray
        ("#64748b", "#f1f5f9", "#ffffff", "Slate Minimal"),
        ("#334155", "#0f172a", "#1e293b", "Night Slate"),
        ("#94a3b8", "#1e293b", "#334155", "Steel"),
        
        # Pastel
        ("#ffafcc", "#ffc8dd", "#ffffff", "Cotton Candy"),
        ("#bde0fe", "#a2d2ff", "#ffffff", "Sky Pastel"),
        ("#cdb4db", "#ffafcc", "#ffffff", "Orchid"),
        
        # Special
        ("#ff0000", "#1a0000", "#330000", "Vampire"),
        ("#ffd700", "#000000", "#111111", "Royal Black"),
        ("#00d4ff", "#002b36", "#073642", "Solarized Ocean"),
    ]

    # Add glass variations
    themes = []
    
    # Generate 60 themes by mixing and matching or adding variations
    for i in range(60):
        # Pick a palette
        p_idx = i % len(palettes)
        primary, bg, card, name = palettes[p_idx]
        
        # Determine mode
        if "(AMOLED)" in name:
            mode = "amoled"
        elif "#f" in bg.lower() and bg.lower() != "#ff0000": # Slack check for light
            mode = "light"
        else:
            mode = "dark"
            
        # Add variation index to name if duplicated
        v_name = f"{name} { (i // len(palettes)) + 1 }" if i >= len(palettes) else name
        
        # Randomize UI details slightly for variety (Store as 0-100 integers)
        glass_blur = random.choice([8, 12, 16, 20])
        glass_opacity = int(random.uniform(0.4, 0.8) * 100)
        nav_opacity = int(random.uniform(0.7, 0.95) * 100)
        accent_opacity = int(random.uniform(0.1, 0.3) * 100)
        glow = int(random.uniform(0.3, 0.7) * 100)
        
        themes.append({
            "name": v_name,
            "description": f"Preset {v_name} for {mode} mode.",
            "theme_type": mode,
            "primary_color": primary,
            "background_color": bg,
            "card_color": card,
            "glass_blur": glass_blur,
            "glass_opacity": glass_opacity,
            "nav_opacity": nav_opacity,
            "accent_opacity": accent_opacity,
            "card_glow_intensity": glow,
            "font_size": 14,
            "cover_width": 120,
            "banner_content_offset": 0
        })
        
    return themes

if __name__ == "__main__":
    import os
    from supabase import create_client
    from dotenv import load_dotenv
    
    load_dotenv()
    
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    
    if not url or not key:
        print("Missing Supabase credentials")
        exit(1)
        
    supabase = create_client(url, key)
    themes = generate_themes()
    
    print(f"Inserting {len(themes)} themes...")
    try:
        # Delete existing themes if you want a clean slate, or just upsert
        # supabase.table('app_themes').delete().neq('id', -1).execute()
        
        # Batch insert
        res = supabase.table('app_themes').upsert(themes).execute()
        print(f"Successfully inserted/updated {len(themes)} themes")
    except Exception as e:
        print(f"Error: {e}")
