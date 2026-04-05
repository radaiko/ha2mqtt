"""Publishes HA entity state changes to MQTT."""

from __future__ import annotations

import json
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

SKIP_ATTRIBUTES = {
    "friendly_name",
    "supported_features",
    "supported_color_modes",
    "entity_picture",
    "icon",
    "assumed_state",
    "attribution",
    "device_class",
    "state_class",
    "unit_of_measurement_precision",
}


class StatePublisher:
    """Listens for state changes and publishes to MQTT."""

    def __init__(self, bridge: Any, resolver: Any, exposure: Any) -> None:
        self._bridge = bridge
        self._resolver = resolver
        self._exposure = exposure

    async def publish_state(self, entity_id: str, state: Any) -> None:
        """Publish an entity's current state and attributes to MQTT."""
        if not self._exposure.is_exposed(entity_id):
            return
        parts = self._resolver.resolve(entity_id)
        if parts is None:
            return
        integration = parts["integration"]
        device_class = parts["device_class"]
        device_name = parts["device_name"]
        topic = self._bridge.build_topic(integration, device_class, device_name, "state")
        await self._bridge.publish(topic, str(state.state))
        for attr_name, attr_value in state.attributes.items():
            if attr_name in SKIP_ATTRIBUTES:
                continue
            topic = self._bridge.build_topic(integration, device_class, device_name, attr_name)
            await self._bridge.publish(topic, self._format_value(attr_value))

    async def publish_all_states(self, hass: Any) -> None:
        """Publish current state of all exposed entities (initial sync)."""
        exposed = self._exposure.get_exposed_entities()
        for entity_id in exposed:
            state = hass.states.get(entity_id)
            if state is not None:
                await self.publish_state(entity_id, state)
        _LOGGER.info("Initial state sync: published %d entities", len(exposed))

    @staticmethod
    def _format_value(value: Any) -> str:
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return str(value)
