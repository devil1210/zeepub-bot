
import sys
import os

# Add the project root to sys.path
sys.path.append(r'c:\Users\charl\Downloads\Zeepub-bot')

print("Attempting to import from models.library_models...")
try:
    from models.library_models import LocalBook, MetadataProposal, SeriesMetadata, TranslatorsGroup, UserDownload
    print("Import successful!")
    print(f"MetadataProposal: {MetadataProposal}")
    print(f"UserDownload: {UserDownload}")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
    import traceback
    traceback.print_exc()
