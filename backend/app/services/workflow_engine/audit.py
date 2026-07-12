from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import json
import os
import logging

logger = logging.getLogger(__name__)


class AuditEvent:
    def __init__(
        self,
        event_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None
    ):
        self.event_type = event_type
        self.description = description
        self.details = details or {}
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "description": self.description,
            "details": self.details
        }


class WorkflowEngine:
    """
    Centralized Workflow & Audit Trail Engine for StatAid Studio.
    Tracks immutable step progression and logs every action for complete scientific reproducibility.
    """
    def __init__(self, log_path: Optional[str] = None):
        self._events: List[AuditEvent] = []
        self._log_path = log_path

    def record_action(
        self,
        event_type: str,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditEvent:
        """Record a timestamped action to the workflow history."""
        event = AuditEvent(event_type=event_type, description=description, details=details)
        self._events.append(event)
        logger.info(f"[Audit Log] {event.timestamp} | {event_type} | {description}")
        if self._log_path:
            self._persist()
        return event

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Return full chronological audit trail."""
        return [ev.to_dict() for ev in self._events]

    def clear(self):
        """Clear current session audit trail."""
        self._events = []

    def _persist(self):
        try:
            if self._log_path:
                with open(self._log_path, "w", encoding="utf-8") as f:
                    json.dump(self.get_audit_trail(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist audit trail to {self._log_path}: {e}")


# Global singleton instance for session-wide audit logging
workflow_engine = WorkflowEngine()
