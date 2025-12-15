import importlib.util
import inspect
from pathlib import Path
from typing import Dict
import logging
from plugins.base_plugin import BasePlugin

class PluginManager:
    def __init__(self, plugin_directory: str = "plugins"):
        self.plugin_directory = Path(plugin_directory)
        self.plugins: Dict[str, BasePlugin] = {}

    async def initialize(self, bot_instance):
        self._bot_instance = bot_instance
        await self.load_all_plugins()

    async def load_all_plugins(self):
        if not self.plugin_directory.exists():
            logging.warning(f"Directorio de plugins no existe: {self.plugin_directory}")
            return
        
        plugin_files = [
            f for f in self.plugin_directory.glob("*.py")
            if f.name not in ["__init__.py", "base_plugin.py", "plugin_manager.py"]
        ]
        
        # Carga concurrente de plugins
        # Nota: La importación en sí es síncrona (limitación de importlib), 
        # pero el metodo .initialize() de cada plugin es asíncrono.
        tasks = [self.load_plugin(f) for f in plugin_files]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def load_plugin(self, plugin_path: Path):
        try:
            spec = importlib.util.spec_from_file_location(plugin_path.stem, plugin_path)
            if not spec or not spec.loader:
                logging.error(f"No se pudo obtener spec para el plugin {plugin_path.name}")
                return

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            plugin_classes = [
                cls for name, cls in inspect.getmembers(module, inspect.isclass)
                if issubclass(cls, BasePlugin) and cls is not BasePlugin
            ]

            if not plugin_classes:
                # Silencioso para archivos auxiliares que no son plugins
                return

            plugin_instance = plugin_classes[0]()
            
            # Inicialización asíncrona
            initialized = await plugin_instance.initialize(self._bot_instance)
            
            if initialized:
                self.plugins[plugin_instance.name] = plugin_instance
                logging.info(f"Plugin cargado: {plugin_instance.name} v{plugin_instance.version}")
            else:
                logging.debug(f"Plugin {plugin_instance.name} no se inicializó (deshabilitado o error).")
                
        except Exception as e:
            logging.error(f"Error cargando plugin {plugin_path.name}: {e}", exc_info=True)

    def get_plugin(self, name: str) -> BasePlugin:
        return self.plugins.get(name)

    def list_plugins(self):
        return {
            name: {
                "version": plugin.version,
                "description": plugin.description
            }
            for name, plugin in self.plugins.items()
        }
