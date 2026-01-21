import asyncio
import os
import sys

# Add root directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from supabase import create_client
from dotenv import load_dotenv

from models.user_models import UserLevel, AppTheme, User
from models.base import Base
from config.config_settings import config

# Force load .env
load_dotenv()

async def get_local_session():
    # Use config.DATABASE_URL but ensure async driver if needed
    db_url = os.getenv("DATABASE_URL")
    
    # Handle SQLite
    if not db_url or "sqlite" in db_url:
        db_path = os.getenv("URL_CACHE_DB_PATH", "data/url_cache.db")
        # Ensure path exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        db_url = f"sqlite+aiosqlite:///{db_path}"
        print(f"🔌 Using SQLite: {db_url}")
    elif "postgresql" in db_url:
        # Ensure async driver
        if "+asyncpg" not in db_url:
             db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
        print(f"🔌 Using Postgres: {db_url}")

    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)()

def get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    if not url or not key:
        print("❌ Supabase credentials missing!")
        sys.exit(1)
    return create_client(url, key)

async def import_data():
    print("🚀 Starting Data Import from Supabase...")
    
    supabase = get_supabase()
    session = await get_local_session()
    
    try:
        # 1. Import User Levels
        print("\n📥 Importing User Levels...")
        res = supabase.table("user_levels").select("*").execute()
        levels_data = res.data
        for item in levels_data:
            # Map/Clean data if necessary
            level = UserLevel(
                id=item.get('id'),
                name=item.get('name'),
                priority=item.get('priority', 0),
                color=item.get('color'),
                ui_theme=item.get('ui_theme'),
                ui_primary_color=item.get('ui_primary_color'),
                ui_font_size=item.get('ui_font_size'),
                ui_nav_opacity=item.get('ui_nav_opacity'),
                ui_glass_blur=item.get('ui_glass_blur'),
                ui_cover_width=item.get('ui_cover_width'),
                ui_accent_opacity=item.get('ui_accent_opacity'),
                panel_transparency=item.get('panel_transparency'),
                background_color=item.get('background_color'),
                card_color=item.get('card_color'),
                banner_content_offset=item.get('banner_content_offset'),
                force_settings=item.get('force_settings', False),
                price=item.get('price', 0.0),
                can_download=item.get('can_download', True),
                can_read=item.get('can_read', True),
                daily_downloads=item.get('daily_downloads', 5),
                has_mini_app_access=item.get('has_mini_app_access', True),
                has_library_access=item.get('has_library_access', True),
                can_request_books=item.get('can_request_books', True),
                early_access=item.get('early_access', False),
                custom_themes=item.get('custom_themes', False),
                allow_theme_templates=item.get('allow_theme_templates', False),
                show_recommendations=item.get('show_recommendations', True)
            )
            await session.merge(level)
        print(f"✅ Synced {len(levels_data)} levels.")

        # 2. Import App Themes
        print("\n📥 Importing App Themes...")
        # Check if table exists in Supabase first (might fail if not created there yet)
        try:
            res = supabase.table("app_themes").select("*").execute()
            themes_data = res.data
            for item in themes_data:
                from dateutil import parser
                theme = AppTheme(
                    id=item.get('id'),
                    name=item.get('name'),
                    description=item.get('description'),
                    theme_type=item.get('theme_type'),
                    primary_color=item.get('primary_color'),
                    background_color=item.get('background_color'),
                    card_color=item.get('card_color'),
                    glass_opacity=item.get('glass_opacity'),
                    nav_opacity=item.get('nav_opacity'),
                    accent_opacity=item.get('accent_opacity'),
                    glass_blur=item.get('glass_blur'),
                    card_glow_intensity=item.get('card_glow_intensity'),
                    font_size=item.get('font_size'),
                    cover_width=item.get('cover_width'),
                    banner_content_offset=item.get('banner_content_offset'),
                    created_at=parser.parse(item.get('created_at')) if item.get('created_at') else None,
                    updated_at=parser.parse(item.get('updated_at')) if item.get('updated_at') else None
                )
                await session.merge(theme)
            print(f"✅ Synced {len(themes_data)} themes.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"⚠️ Could not sync themes: {e}")

        # 3. Import Users (Optional - Just Admin)
        print("\n📥 Importing Admin Users...")
        admin_ids = [int(uid.strip()) for uid in os.getenv("ADMIN_USERS", "").split(",") if uid.strip()]
        if admin_ids:
            res = supabase.table("users").select("*").in_("telegram_id", admin_ids).execute()
            users_data = res.data
            for item in users_data:
                user = User(
                    telegram_id=item.get('telegram_id'),
                    username=item.get('username'),
                    name=item.get('name'),
                    nickname=item.get('nickname'),
                    photo_url=item.get('photo_url'),
                    level_id=item.get('level_id'),
                    role=item.get('role'),
                    beta_tester=item.get('beta_tester'),
                    has_library_access=item.get('has_library_access'),
                    can_request_books=item.get('can_request_books'),
                    total_downloads=item.get('total_downloads'),
                    insignias=item.get('insignias'),
                    settings=item.get('settings'),
                    expires_at=item.get('expires_at')
                )
                await session.merge(user)
            print(f"✅ Synced {len(users_data)} admin users.")
        
        await session.commit()
        print("\n🎉 Import Completed Successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during import: {e}")
        await session.rollback()
    finally:
        await session.close()

if __name__ == "__main__":
    try:
        asyncio.run(import_data())
    except KeyboardInterrupt:
        print("Cancelled.")
