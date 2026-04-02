# src/utils/templates.py
import re
from typing import Any, Dict

def render_template(template: str, data: Dict[str, Any]) -> str:
    """
    Renderizador de plantillas estilo Zeepub.
    Soporta bloques condicionales [?var]...[/?].
    """
    # 1. Procesar bloques condicionales [?var]...[/?]
    def replace_conditional(match):
        var_name = match.group(1)
        content = match.group(2)
        # Si la variable existe y no es vacía/falsa
        if data.get(var_name):
            return content
        return ""

    # Regex para [?variable]contenido[/?]
    rendered = re.sub(r"\[\?(\w+)\](.*?)\[/\?\]", replace_conditional, template, flags=re.DOTALL)

    # 2. Reemplazar placeholders básicos {variable}
    for key, value in data.items():
        placeholder = "{" + str(key) + "}"
        rendered = rendered.replace(placeholder, str(value) if value is not None else "")

    # Limpiar saltos de línea excesivos
    rendered = re.sub(r"\n{3,}", "\n\n", rendered)
    
    return rendered.strip()
