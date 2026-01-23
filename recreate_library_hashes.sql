-- Reinicio de la tabla local_books con la nueva estructura de hashes
-- Ejecutar este script en el Editor SQL de Supabase o en tu cliente Postgres

-- 1. Opcional: Respaldar valoraciones existentes asociándolas a los nuevos hashes
-- Nota: Esto solo funciona si ejecutas esto ANTES de borrar local_books.
-- Si prefieres empezar de cero, sáltate al paso 2.

-- 2. Eliminar tabla local_books para regenerar hashes limpios
DROP TABLE IF EXISTS duplicate_books;
DROP TABLE IF EXISTS local_books CASCADE;

-- 3. Recrear tabla local_books (SQLAlchemy la recreará automáticamente al iniciar el bot, 
-- pero aquí tienes la definición manual para asegurar los índices)
CREATE TABLE local_books (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES library_sources(id),
    filepath TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    file_size BIGINT,
    file_type TEXT,
    title TEXT NOT NULL,
    author TEXT,
    series TEXT,
    series_index TEXT,
    indexed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP WITH TIME ZONE,
    romaji_title TEXT,
    english_title TEXT,
    internal_title TEXT,
    clean_title TEXT,
    summary TEXT,
    publisher TEXT,
    translator TEXT,
    layout_by TEXT,
    book_type TEXT,
    year TEXT,
    language TEXT DEFAULT 'es',
    isbn TEXT,
    asin TEXT,
    cover TEXT,
    cover_low TEXT,
    tags JSONB,
    demographics JSONB,
    categories JSONB,
    epub_version TEXT,
    rating_average FLOAT DEFAULT 0.0,
    rating_count INTEGER DEFAULT 0,
    page_count TEXT,
    word_count TEXT,
    reading_time TEXT,
    series_hash VARCHAR(64),
    book_hash VARCHAR(64) UNIQUE
);

CREATE INDEX idx_local_books_book_hash ON local_books(book_hash);
CREATE INDEX idx_local_books_series_hash ON local_books(series_hash);

-- 4. Actualizar tabla de valoraciones para usar book_hash
ALTER TABLE user_ratings ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_user_ratings_book_hash ON user_ratings(book_hash);

-- 5. Actualizar tabla de descargas (ya debería tener book_hash, pero aseguramos)
ALTER TABLE user_downloads ADD COLUMN IF NOT EXISTS book_hash VARCHAR(64);
CREATE INDEX IF NOT EXISTS idx_user_downloads_book_hash ON user_downloads(book_hash);

-- NOTA FINAL:
-- Una vez ejecutado esto, reinicia el bot y ejecuta /scan_library.
-- Los nuevos hashes se generarán según: series + author + book_type + volume + translator + maquetador.
