from .base import Base
from .download_models import DownloadHistory
from .library_models import (
    AILearningFeedback,
    LibrarySource,
    LocalBook,
    MetadataProposal,
    SeriesMetadata,
    TranslatorsGroup,
    UploadBook,
    UploadHistory,
    UserDownload,
    UserRating,
)
from .user_models import AppTheme, User, UserLevel, UserUISettings

# This ensures that when we import 'models', all classes are registered with Base.metadata
__all__ = [
    "Base",
    "User",
    "UserLevel",
    "UserUISettings",
    "AppTheme",
    "SeriesMetadata",
    "LocalBook",
    "TranslatorsGroup",
    "LibrarySource",
    "UploadBook",
    "UploadHistory",
    "UserRating",
    "UserDownload",
    "AILearningFeedback",
    "MetadataProposal",
    "DownloadHistory",
]
