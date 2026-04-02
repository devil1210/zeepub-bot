import os

def extract_registry():
    plugin_path = os.path.join("plugins", "custom_messages_plugin.py")
    target_path = os.path.join("utils", "template_registry_data.py")
    
    with open(plugin_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    # lines 35:1466 (0-indexed means lines[35] is line 36)
    registry_lines = lines[35:1466]
    
    with open(target_path, "w", encoding="utf-8") as f:
        f.write('"""\nRegistro de plantillas y variables globales.\nExtraído de custom_messages_plugin.py\n"""\n\n')
        f.writelines(registry_lines)
        
    print(f"Extracted {len(registry_lines)} lines to {target_path}")

if __name__ == "__main__":
    extract_registry()
