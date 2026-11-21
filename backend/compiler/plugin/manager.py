import os
import importlib
from .base import PluginBase
from .timing import TimingPlugin


_BUILTIN_PLUGINS = {
    "Timing": TimingPlugin,
}


class PluginManager:
    def __init__(self):
        self._plugins = []

    def load_builtins(self):
        for name, cls in _BUILTIN_PLUGINS.items():
            if not any(p.name == name for p in self._plugins):
                self._plugins.append(cls())

    def load_from_env(self, env_var="CYTOLOGIC_PLUGINS"):
        modules = os.environ.get(env_var, "")
        if not modules:
            return
        for module_path in modules.split(","):
            module_path = module_path.strip()
            if module_path:
                self._load_module(module_path)

    def _load_module(self, module_path):
        try:
            mod = importlib.import_module(module_path)
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, PluginBase) and
                    attr is not PluginBase):
                    plugin = attr()
                    if not any(p.name == plugin.name for p in self._plugins):
                        self._plugins.append(plugin)
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to load plugin {module_path}: {e}")

    def register(self, plugin):
        if isinstance(plugin, type) and issubclass(plugin, PluginBase):
            plugin = plugin()
        if isinstance(plugin, PluginBase):
            if not any(p.name == plugin.name for p in self._plugins):
                self._plugins.append(plugin)

    @property
    def plugins(self):
        return list(self._plugins)

    def invoke(self, hook_name, *args, **kwargs):
        results = []
        for plugin in self._plugins:
            method = getattr(plugin, hook_name, None)
            if method is None:
                continue
            try:
                result = method(*args, **kwargs)
                if result is not None:
                    results.append((plugin.name, result))
            except Exception as e:
                import warnings
                warnings.warn(
                    f"Plugin {plugin.name}.{hook_name} raised: {e}"
                )
        return results


_GLOBAL_MANAGER = None


def get_manager():
    global _GLOBAL_MANAGER
    if _GLOBAL_MANAGER is None:
        _GLOBAL_MANAGER = PluginManager()
        _GLOBAL_MANAGER.load_builtins()
        _GLOBAL_MANAGER.load_from_env()
    return _GLOBAL_MANAGER


def reset_manager():
    global _GLOBAL_MANAGER
    _GLOBAL_MANAGER = None
