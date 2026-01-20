-- Add missing UI columns to user_levels table
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS background_color text DEFAULT '#0f172a';
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS card_color text DEFAULT '#1e293b';
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS banner_content_offset integer DEFAULT 0;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS force_settings boolean DEFAULT false;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS ui_primary_color text DEFAULT '#2b6cee';
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS ui_theme text DEFAULT 'dark';
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS ui_font_size integer DEFAULT 14;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS ui_glass_blur integer DEFAULT 12;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS ui_cover_width integer DEFAULT 120;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS ui_nav_opacity float DEFAULT 0.8;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS ui_accent_opacity float DEFAULT 0.2;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS panel_transparency integer DEFAULT 60;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS can_download boolean DEFAULT true;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS can_read boolean DEFAULT true;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS has_library_access boolean DEFAULT true;
ALTER TABLE user_levels ADD COLUMN IF NOT EXISTS can_request_books boolean DEFAULT true;
