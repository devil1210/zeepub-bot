from .agent_models import AgentExecution
from .audit_models import MetadataAudit
from .base import Base
from .communications import (
    DiscoveredChat,
    PublicationChannel,
    PublicationQueue,
    PublicationTemplate,
)
from .custom_messages_models import GlobalVariable, PluginSettings, StoredMessage
from .download_models import DownloadHistory
from .group_models import GroupSettings
from .library import (
    AILearningFeedback,
    ArchivedBook,
    ArchivedSeries,
    BookWorkgroup,
    Demographic,
    Genre,
    GroupContactLink,
    LibraryCleanupLog,
    LibrarySource,
    LocalBook,
    MediaAsset,
    MetadataProposal,
    SeriesAlias,
    SeriesMetadata,
    TranslatorsGroup,
    UploadBook,
    UploadHistory,
    UserDownload,
    UserRating,
    Workgroup,
)
from .theme_sync_models import ThemeSyncLog
from .user_audit_models import UserAuditLog
from .users import AppTheme, User, UserLevel, UserUISettings

# This ensures that when we import 'models', all classes are registered with Base.metadata
__all__ = [
    "AILearningFeedback",
    "AgentExecution",
    "AppTheme",
    "ArchivedBook",
    "ArchivedSeries",
    "Base",
    "BookWorkgroup",
    "Demographic",
    "DiscoveredChat",
    "DownloadHistory",
    "Genre",
    "GlobalVariable",
    "GroupContactLink",
    "GroupSettings",
    "LibraryCleanupLog",
    "LibrarySource",
    "LocalBook",
    "MediaAsset",
    "MetadataAudit",
    "MetadataProposal",
    "PluginSettings",
    "PublicationChannel",
    "PublicationQueue",
    "PublicationTemplate",
    "SeriesAlias",
    "SeriesMetadata",
    "StoredMessage",
    "ThemeSyncLog",
    "TranslatorsGroup",
    "UploadBook",
    "UploadHistory",
    "User",
    "UserAuditLog",
    "UserDownload",
    "UserLevel",
    "UserRating",
    "UserUISettings",
    "Workgroup",
]
