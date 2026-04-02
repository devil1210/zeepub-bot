
import sys
import os

# Add the project root to sys.path
sys.path.append(r'c:\Users\charl\Downloads\Zeepub-bot')

try:
    from models.library_models import MetadataProposal
    print("Import successful!")
except ImportError as e:
    print(f"Import failed: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
