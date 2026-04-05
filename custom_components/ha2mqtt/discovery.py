"""Optional MQTT discovery publisher for HA2MQTT."""

from __future__ import annotations

import json
import logging
from typing import Any

from .const import SERVICE_MAP

_LOGGER = logging.getLogger(__name__)

# Domains that support command topics
SETTABLE_DOMAINS = set(SERVICE_MAP.keys())


class DiscoveryPublisher:
    """Publishes MQTT discovery config messages."""

    def __init__(self, bridge: Any, discovery_prefix: str = "homeassistant") -> None:
        self._bridge = bridge
        self._prefix = discovery_prefix

    def _discovery_topic(self, domain: str, entity_id: str) -> str:
        """Build the discovery config topic."""
        unique_id = f"ha2mqtt_{entity_id.replace('.', '_')}"
        return f"{self._prefix}/{domain}/{unique_id}/config"

    async def publish_discovery(
        self,
        entity_id: str,
        integration: str,
        device_class: str,
        device_name: str,
        attributes: list[str],
    ) -> None:
        """Publish a discovery config for an entity."""
        topic = self._discovery_topic(device_class, entity_id)

        state_topic = self._bridge.build_topic(integration, device_class, device_name, "state")

        config: dict[str, Any] = {
            "name": device_name,
            "unique_id": f"ha2mqtt_{entity_id.replace('.', '_')}",
            "state_topic": state_topic,
            "availability_topic": self._bridge.availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",
        }

        if device_class in SETTABLE_DOMAINS:
            config["command_topic"] = state_topic + "/set"

        if device_class == "light" and "brightness" in attributes:
            brightness_topic = self._bridge.build_topic(integration, device_class, device_name, "brightness")
            config["brightness_state_topic"] = brightness_topic
            config["brightness_command_topic"] = brightness_topic + "/set"

        if device_class == "light" and "color_temp" in attributes:
            color_temp_topic = self._bridge.build_topic(integration, device_class, device_name, "color_temp")
            config["color_temp_state_topic"] = color_temp_topic
            config["color_temp_command_topic"] = color_temp_topic + "/set"

        payload = json.dumps(config)
        await self._bridge.publish(topic, payload, retain=True)
        _LOGGER.debug("Published discovery for %s", entity_id)

    async def remove_discovery(self, domain: str, entity_id: str) -> None:
        """Remove a discovery config by publishing empty payload."""
        topic = self._discovery_topic(domain, entity_id)
        await self._bridge.publish(topic, "", retain=True)
        _LOGGER.debug("Removed discovery for %s", entity_id)

    async def publish_all(self, exposed_entities: dict[str, dict], hass: Any) -> None:
        """Publish discovery configs for all exposed entities."""
        for entity_id, info in exposed_entities.items():
            state = hass.states.get(entity_id)
            attributes = list(state.attributes.keys()) if state else []
            await self.publish_discovery(
                entity_id=entity_id,
                integration=info["integration"],
                device_class=info["domain"],
                device_name=info.get("device_name_slug", entity_id),
                attributes=attributes,
            )

    async def remove_all(self, exposed_entities: dict[str, dict]) -> None:
        """Remove discovery configs for all exposed entities."""
        for entity_id, info in exposed_entities.items():
            await self.remove_discovery(info["domain"], entity_id)
