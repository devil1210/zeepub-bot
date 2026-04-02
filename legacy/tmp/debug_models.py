
import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from models.user_models import DownloadLog
from models.library_models import UserDownload

print(f"DownloadLog attributes: {dir(DownloadLog)}")
print(f"UserDownload attributes: {dir(UserDownload)}")
print(f"Are they the same? {DownloadLog is UserDownload}")
print(f"Does DownloadLog have series_hash? {hasattr(DownloadLog, 'series_hash')}")
