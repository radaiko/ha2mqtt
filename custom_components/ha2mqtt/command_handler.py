"""Handles inbound MQTT commands and routes them to HA services."""

from __future__ import annotations

import json
import logging
from typing import Any

from .const import SERVICE_MAP

_LOGGER = logging.getLogger(__name__)


class CommandHandler:
    """Parses MQTT set messages and calls HA services."""

    def __init__(self, hass: Any, resolver: Any, topic_prefix: str = "") -> None:
        self._hass = hass
        self._resolver = resolver
        self._topic_prefix = topic_prefix

    async def handle_message(self, topic: str, payload: str) -> None:
        """Handle an incoming MQTT set message."""
        parts = self._parse_topic(topic)
        if parts is None:
            _LOGGER.warning("Could not parse set topic: %s", topic)
            return

        integration, device_name, device_class, entity_key, attribute = parts

        entity_id = self._resolver.get_entity_id(integration, device_class, device_name, entity_key)
        if entity_id is None:
            _LOGGER.warning(
                "No entity found for %s/%s/%s/%s", integration, device_class, device_name, entity_key
            )
            return

        domain = entity_id.split(".")[0]

        domain_map = SERVICE_MAP.get(domain)
        if domain_map is None:
            _LOGGER.warning("No service mapping for domain: %s", domain)
            return

        attr_map = domain_map.get(attribute)
        if attr_map is None:
            _LOGGER.warning("No service mapping for %s.%s", domain, attribute)
            return

        await self._call_service(entity_id, domain, attr_map, payload)

    def _parse_topic(self, topic: str) -> tuple[str, str, str, str, str] | None:
        """Parse a set topic into (integration, domain, device, entity_key, attribute).

        Formats:
          [prefix/]integration/domain/device/entity_key/set          → attribute="state"
          [prefix/]integration/domain/device/entity_key/attribute/set
        """
        parts = topic.split("/")
        if not parts or parts[-1] != "set":
            return None
        parts = parts[:-1]
        if self._topic_prefix:
            prefix_parts = self._topic_prefix.split("/")
            if parts[: len(prefix_parts)] == prefix_parts:
                parts = parts[len(prefix_parts) :]
        if len(parts) == 4:
            # integration/domain/device/entity_key → attribute defaults to "state"
            return parts[0], parts[1], parts[2], parts[3], "state"
        if len(parts) == 5:
            # integration/domain/device/entity_key/attribute
            return parts[0], parts[1], parts[2], parts[3], parts[4]
        return None

    async def _call_service(self, entity_id: str, domain: str, attr_map: dict, payload: str) -> None:
        """Call the appropriate HA service."""
        service_data = {"entity_id": entity_id}

        if "on" in attr_map and "off" in attr_map:
            value = payload.lower()
            if value in ("on", "open", "lock"):
                service_call = attr_map["on"]
            elif value in ("off", "close", "unlock"):
                service_call = attr_map["off"]
            else:
                _LOGGER.warning("Unknown toggle value for %s: %s", entity_id, payload)
                return
        elif "trigger" in attr_map:
            service_call = attr_map["service"]
        elif "service" in attr_map:
            service_call = attr_map["service"]
            attr_key = attr_map["attr"]
            value_type = attr_map["type"]
            if value_type == "rgb":
                service_data[attr_key] = json.loads(payload)
            elif value_type == int:
                service_data[attr_key] = int(float(payload))
            elif value_type == float:
                service_data[attr_key] = float(payload)
            else:
                service_data[attr_key] = payload
        else:
            _LOGGER.warning("Unknown mapping format for %s", entity_id)
            return

        svc_domain, svc_name = service_call.split(".", 1)
        await self._hass.services.async_call(svc_domain, svc_name, service_data)
        _LOGGER.debug("Called %s with %s", service_call, service_data)
