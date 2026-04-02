import os

def replace_in_plugin():
    plugin_path = os.path.join("plugins", "custom_messages_plugin.py")
    
    with open(plugin_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    new_lines = lines[:36] + ["from utils.template_registry_data import TEMPLATE_REGISTRY, GLOBAL_VARIABLES\n"] + lines[1465:]
    
    with open(plugin_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)
        
    print(f"Replaced lines in {plugin_path}")

if __name__ == "__main__":
    replace_in_plugin()
