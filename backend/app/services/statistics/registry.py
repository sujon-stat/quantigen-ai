from typing import Dict, List, Optional, Any
from backend.app.services.statistics.base import BaseStatisticalMethod


class MethodRegistry:
    """Registry for discovering, registering, and retrieving statistical methods."""
    _methods: Dict[str, BaseStatisticalMethod] = {}

    @classmethod
    def register(cls, method_instance: BaseStatisticalMethod) -> None:
        """Register a statistical method instance."""
        cls._methods[method_instance.method_id] = method_instance

    @classmethod
    def get(cls, method_id: str) -> Optional[BaseStatisticalMethod]:
        """Get a registered method instance by ID."""
        return cls._methods.get(method_id)

    @classmethod
    def list_all(cls) -> List[Dict[str, Any]]:
        """List summary metadata for all registered statistical methods."""
        return [
            {
                "method_id": m.method_id,
                "name": m.method_name,
                "family": m.method_family,
                "description": m.description,
                "required_variables": m.required_variables,
                "optional_variables": m.optional_variables
            }
            for m in cls._methods.values()
        ]

    @classmethod
    def clear(cls) -> None:
        """Clear the registry (useful for testing)."""
        cls._methods.clear()
