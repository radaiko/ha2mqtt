"""Manages which integrations and devices are exposed to MQTT."""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class ExposureManager:
    """Determines which entities should be bridged to MQTT."""

    def __init__(self, exposed_integrations: list[str], excluded_devices: list[str]) -> None:
        self._exposed_integrations = set(exposed_integrations)
        self._excluded_devices = set(excluded_devices)
        self._exposed: dict[str, dict[str, Any]] = {}
        self._entry_to_integration: dict[str, str] = {}

    def rebuild(self, devices: dict[str, Any], entities: list[Any], config_entries: dict[str, Any]) -> None:
        """Rebuild the exposure map from current registries."""
        self._exposed.clear()
        self._entry_to_integration = {entry_id: entry.domain for entry_id, entry in config_entries.items()}
        device_info: dict[str, tuple[str, str]] = {}
        for device_id, device in devices.items():
            integration = self._get_device_integration(device)
            if integration and integration in self._exposed_integrations:
                if device_id not in self._excluded_devices:
                    name = device.name_by_user or device.name or device_id
                    device_info[device_id] = (integration, name)
        for entity in entities:
            if entity.disabled:
                continue
            if entity.device_id is None:
                continue
            if entity.device_id not in device_info:
                continue
            integration, device_name = device_info[entity.device_id]
            self._exposed[entity.entity_id] = {
                "integration": integration,
                "device_name": device_name,
                "domain": entity.domain,
                "device_id": entity.device_id,
            }
        _LOGGER.info("Exposure map rebuilt: %d entities exposed", len(self._exposed))

    def _get_device_integration(self, device: Any) -> str | None:
        for entry_id in device.config_entries:
            if entry_id in self._entry_to_integration:
                return self._entry_to_integration[entry_id]
        return None

    def is_exposed(self, entity_id: str) -> bool:
        return entity_id in self._exposed

    def get_exposed_entities(self) -> dict[str, dict[str, Any]]:
        return dict(self._exposed)

    def get_entity_info(self, entity_id: str) -> dict[str, Any] | None:
        return self._exposed.get(entity_id)

    def update_config(self, exposed_integrations: list[str], excluded_devices: list[str]) -> None:
        self._exposed_integrations = set(exposed_integrations)
        self._excluded_devices = set(excluded_devices)
