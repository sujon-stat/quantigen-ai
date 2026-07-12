import os
import json
import importlib
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PluginManifest(BaseModel):
    """
    Plugin Manifest defining metadata, permissions, dependencies, and registered capabilities.
    Isolates third-party and institutional extensions from the core engine.
    """
    id: str = Field(..., description="Unique plugin identifier (e.g. 'survival-suite-v2')")
    name: str = Field(..., description="Human-readable plugin name")
    version: str = Field("1.0.0", description="Semantic version string")
    author: str = Field("StatAid Community", description="Plugin creator or institution")
    description: str = Field(..., description="Brief summary of statistical methods or data parsers provided")
    dependencies: List[str] = Field(default_factory=list, description="Required Python or R libraries (e.g. ['lifelines', 'rpy2'])")
    permissions: List[str] = Field(default_factory=list, description="Requested execution permissions (e.g. ['read_dataset', 'execute_r'])")
    entry_point: Optional[str] = Field(None, description="Python module path to load on startup (e.g. 'plugins.survival.main')")
    provides_methods: List[str] = Field(default_factory=list, description="List of method IDs registered by this plugin")
    provides_parsers: List[str] = Field(default_factory=list, description="List of parser IDs registered by this plugin")


class PluginManager:
    """
    Centralized Plugin Manager responsible for discovering, validating, and loading external extensions.
    Ensures that custom institutional methods or parsers can be injected cleanly without modifying core modules.
    """
    def __init__(self, plugin_dir: Optional[str] = None):
        self.plugin_dir = plugin_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "plugins")
        self._manifests: Dict[str, PluginManifest] = {}
        self._loaded_modules: Dict[str, Any] = {}

    def discover_and_load(self) -> List[PluginManifest]:
        """Scan plugin directory for valid manifest.json files and register their capabilities."""
        if not os.path.exists(self.plugin_dir):
            os.makedirs(self.plugin_dir, exist_ok=True)
            return []

        loaded = []
        for root, dirs, files in os.walk(self.plugin_dir):
            if "manifest.json" in files:
                manifest_path = os.path.join(root, "manifest.json")
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    manifest = PluginManifest(**data)
                    self._manifests[manifest.id] = manifest
                    logger.info(f"[Plugin Engine] Discovered plugin manifest: {manifest.name} ({manifest.id})")
                    
                    if manifest.entry_point:
                        self._load_entry_point(manifest)
                    loaded.append(manifest)
                except Exception as e:
                    logger.error(f"[Plugin Engine] Failed to load plugin manifest from {manifest_path}: {e}")
        return loaded

    def _load_entry_point(self, manifest: PluginManifest):
        """Dynamically import the plugin's Python entry point module."""
        try:
            mod = importlib.import_module(manifest.entry_point)
            self._loaded_modules[manifest.id] = mod
            if hasattr(mod, "register_plugin"):
                mod.register_plugin()
            logger.info(f"[Plugin Engine] Successfully loaded entry point for plugin '{manifest.id}'")
        except Exception as e:
            logger.error(f"[Plugin Engine] Error loading entry point '{manifest.entry_point}' for plugin '{manifest.id}': {e}")

    def list_plugins(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered plugins."""
        return [m.model_dump() for m in self._manifests.values()]

    def register_manifest(self, manifest: PluginManifest) -> PluginManifest:
        """Dynamically register a plugin manifest."""
        self._manifests[manifest.id] = manifest
        return manifest


# Singleton plugin manager instance
plugin_manager = PluginManager()
