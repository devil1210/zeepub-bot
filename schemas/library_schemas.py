from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime

class CoverUrlDTO(BaseModel):
    cover_low: Optional[str] = None
    cover_medium: Optional[str] = None
    cover_high: Optional[str] = None
    cover_original: Optional[str] = None
    cover: Optional[str] = None

class BookDTO(BaseModel):
    id: Any
    title: str
    cleanTitle: Optional[str] = None
    author: Optional[str] = None
    series: Optional[str] = None
    volume: Optional[float] = None
    book_type: Optional[str] = None
    cover: Optional[str] = None
    coverUrl: Optional[str] = None # Simplified path for some views
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    book_hash: Optional[str] = None
    series_hash: Optional[str] = None
    download_count: int = 0
    rating_average: float = 0.0
    rating_count: int = 0
    is_folder: bool = False
    
    # Enrichment
    romaji_title: Optional[str] = None
    english_title: Optional[str] = None
    spanish_title: Optional[str] = None
    translator: Optional[str] = None
    illustrator: Optional[str] = None
    layout_by: Optional[str] = None
    publisher: Optional[str] = None
    isbn: Optional[str] = None
    modifiedAt: Optional[str] = None
    
    # Explicit compatibility fields
    is_uncensored: bool = False
    color_mode: Optional[str] = None

class SeriesDTO(BaseModel):
    id: str
    series_hash: str
    title: str
    series: str
    series_spanish: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    cover: Optional[str] = None
    coverUrl: Optional[CoverUrlDTO] = None
    numBooks: int = 0
    rating_average: float = 0.0
    rating_count: int = 0
    is_series: bool = True
    type: str = "series"
    lastUpdated: Optional[str] = None

class DownloadStatsDTO(BaseModel):
    used: int
    limit: int
    total: int

class UserDTO(BaseModel):
    user_id: int
    username: Optional[str] = None
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
    results: List[Any]
    items: List[Any]
    currentPage: int
    page: int
    totalPages: int
    totalItems: int
    total: int

class DownloadHistoryItemDTO(BaseModel):
    id: int
    title: str
    cover: Optional[str] = None
    downloaded_at: str
    book_hash: str
