from typing import Any

from pydantic import BaseModel, Field


class CoverUrlDTO(BaseModel):
    cover_low: str | None = None
    cover_medium: str | None = None
    cover_high: str | None = None
    cover_original: str | None = None
    cover: str | None = None


class BookDTO(BaseModel):
    id: Any
    title: str
    cleanTitle: str | None = None
    author: str | None = None
    series: str | None = None
    series_english: str | None = None
    volume: float | None = None
    book_type: str | None = None
    cover: str | None = None
    coverUrl: str | None = None  # Simplified path for some views

    # Detailed Cover Paths
    cover_low: str | None = None
    cover_medium: str | None = None
    cover_high: str | None = None
    cover_original: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    demographics: list[str] | None = None
    book_hash: str | None = None
    series_hash: str | None = None
    download_count: int = 0
    rating_average: float = 0.0
    rating_count: int = 0
    is_folder: bool = False

    # Enrichment
    romaji_title: str | None = None
    english_title: str | None = None
    spanish_title: str | None = None
    translator: str | None = None
    illustrator: str | None = None
    layout_by: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    modifiedAt: str | None = None
    published_at: str | None = None
    asin: str | None = None
    word_count: int | None = None
    page_count: int | None = None
    reading_time: int | None = None
    file_size: int | None = None
    size: str | None = None
    epub_version: str | None = None
    modified_at_opf: str | None = None
    group: str | None = None
    volumeNumber: float | None = None

    # Explicit compatibility fields
    is_uncensored: bool = False
    color_mode: str | None = None


class SeriesDTO(BaseModel):
    id: str
    series_hash: str
    title: str
    series: str
    series_spanish: str | None = None
    series_english: str | None = None
    author: str | None = None
    description: str | None = None
    cover: str | None = None
    coverUrl: CoverUrlDTO | None = None
    numBooks: int = 0
    book_type: str | None = None
    format: str = "EPUB"
    rating_average: float = 0.0
    rating_count: int = 0
    is_series: bool = True
    type: str = "series"
    illustrator: str | None = None
    translator: str | None = None
    layout_by: str | None = None
    lastUpdated: str | None = None


class DownloadStatsDTO(BaseModel):
    used: int
    limit: int
    total: int


class UserDTO(BaseModel):
    user_id: int
    username: str | None = None
    role: str
    status_label: str
    downloads: DownloadStatsDTO
    has_mini_app_access: bool
    can_request_books: bool
    can_upload_epub: bool


class UserStatusDTO(BaseModel):
    user: UserDTO
    hasUnlimitedDownloads: bool
    isStaff: bool
    isAdmin: bool


class PaginatedResponse(BaseModel):
    results: list[Any]
    items: list[Any]
    currentPage: int
    page: int
    totalPages: int
    totalItems: int
    total: int


class DownloadHistoryItemDTO(BaseModel):
    id: int
    title: str
    cover: str | None = None
    downloaded_at: str
    book_hash: str
