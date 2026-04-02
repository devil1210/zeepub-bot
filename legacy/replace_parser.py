import os

def refactor_parser():
    plugin_path = os.path.join("plugins", "custom_messages_plugin.py")
    
    with open(plugin_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if "async def _get_extended_user_context" in line:
            start_idx = i
        if "async def get_web_strings" in line:
            end_idx = i - 1
            break
            
    if start_idx != -1 and end_idx != -1:
        new_method = '''    async def get_text(self, slug: str, default_text: str = None, user=None, **replacements) -> str:
        """
        Recupera el texto de un mensaje guardado por su slug,
        delegando la lógica de renderizado a utils.template_parser.
        """
        msg = self._get_message(slug.lower())
        db_text = msg.text_content if msg else None

        bot_info = None
        if self.bot:
            bot_info = {
                "first_name": getattr(self.bot, "first_name", "Bot"),
                "username": getattr(self.bot, "username", "Bot")
            }

        from utils.template_parser import render_template
        return await render_template(
            slug=slug,
            db_text=db_text,
            default_text=default_text,
            user=user,
            global_vars_cache=self._global_vars_cache,
            bot_info=bot_info,
            **replacements
        )

'''
        lines = lines[:start_idx] + [new_method] + lines[end_idx+1:]
        
        with open(plugin_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print("Parser refactored successfully.")
    else:
        print(f"Couldn't find the methods. start: {start_idx}, end: {end_idx}")

if __name__ == "__main__":
    refactor_parser()
