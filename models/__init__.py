from .agent_models import AgentExecution
from .audit_models import MetadataAudit
from .base import Base
from .custom_messages_models import GlobalVariable, PluginSettings, StoredMessage
from .download_models import DownloadHistory
from .group_models import GroupSettings
from .library_models import (
    AILearningFeedback,
    ArchivedBook,
    ArchivedSeries,
    Demographic,
    Genre,
    LibraryCleanupLog,
    LibrarySource,
    LocalBook,
    MediaAsset,
    MetadataProposal,
    SeriesMetadata,
    TranslatorsGroup,
    UploadBook,
    UploadHistory,
    UserDownload,
    UserRating,
)
from .publication_models import (
    DiscoveredChat,
    PublicationChannel,
    PublicationQueue,
    PublicationTemplate,
)
from .theme_sync_models import ThemeSyncLog
from .user_audit_models import UserAuditLog
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
    "Genre",
    "Demographic",
    "MediaAsset",
    "ArchivedBook",
    "ArchivedSeries",
    "LibraryCleanupLog",
    "PublicationChannel",
    "PublicationTemplate",
    "PublicationQueue",
    "DiscoveredChat",
    "ThemeSyncLog",
    "UserAuditLog",
    "MetadataAudit",
    "AgentExecution",
    "StoredMessage",
    "PluginSettings",
    "GlobalVariable",
    "GroupSettings",
]
