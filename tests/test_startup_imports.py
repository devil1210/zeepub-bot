
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

def test_imports():
    try:
        print("Importing handlers.callback_handlers...")
        import handlers.callback_handlers
        print("Success.")
        
        print("Importing handlers.message_handlers...")
        import handlers.message_handlers
        print("Success.")
        
        print("Importing handlers.command_handlers...")
        import handlers.command_handlers
        print("Success.")
        
        print("All handlers imported successfully. No ModuleNotFoundError for opds_service.")
    except ImportError as e:
        import traceback
        traceback.print_exc()
        print(f"IMPORT ERROR: {e}")
        exit(1)
    except Exception as e:
        print(f"OTHER ERROR: {e}")
        # We might get other errors due to missing config/env, but we looking for opds_service specifically
        if "opds_service" in str(e):
             exit(1)
        # Ignore other startup errors like DB connection for this test
        pass

if __name__ == "__main__":
    test_imports()
