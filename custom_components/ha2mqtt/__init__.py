"""The HA2MQTT integration."""

from __future__ import annotations

import logging
from typing import Any

try:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.const import EVENT_STATE_CHANGED
    from homeassistant.core import Event, HomeAssistant
    from homeassistant.helpers import device_registry as dr, entity_registry as er
except ImportError:
    ConfigEntry = Any
    HomeAssistant = Any
    Event = Any
    EVENT_STATE_CHANGED = "state_changed"
    dr = None
    er = None

from .command_handler import CommandHandler
from .const import (
    CONF_BROKER_HOST,
    CONF_BROKER_PASSWORD,
    CONF_BROKER_PORT,
    CONF_BROKER_TLS,
    CONF_BROKER_USERNAME,
    CONF_DISCOVERY_ENABLED,
    CONF_DISCOVERY_PREFIX,
    CONF_EXCLUDED_DEVICES,
    CONF_EXPOSED_INTEGRATIONS,
    CONF_QOS,
    CONF_RETAIN,
    CONF_TOPIC_PREFIX,
    DOMAIN,
)
from .device_resolver import DeviceResolver, slugify_name
from .discovery import DiscoveryPublisher
from .exposure_manager import ExposureManager
from .mqtt_bridge import MQTTBridge
from .state_publisher import StatePublisher

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA2MQTT from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    bridge_config = {
        "host": entry.data[CONF_BROKER_HOST],
        "port": entry.data[CONF_BROKER_PORT],
        "username": entry.data.get(CONF_BROKER_USERNAME) or None,
        "password": entry.data.get(CONF_BROKER_PASSWORD) or None,
        "tls": entry.data.get(CONF_BROKER_TLS, False),
        "topic_prefix": entry.data.get(CONF_TOPIC_PREFIX, ""),
        "retain": entry.data.get(CONF_RETAIN, True),
        "qos": entry.data.get(CONF_QOS, 0),
    }

    bridge = MQTTBridge(bridge_config)
    resolver = DeviceResolver()
    exposure = ExposureManager(
        exposed_integrations=entry.options.get(CONF_EXPOSED_INTEGRATIONS, []),
        excluded_devices=entry.options.get(CONF_EXCLUDED_DEVICES, []),
    )
    publisher = StatePublisher(bridge, resolver, exposure)
    handler = CommandHandler(hass, resolver, topic_prefix=bridge_config["topic_prefix"])

    # Create discovery publisher if enabled
    discovery = None
    if entry.data.get(CONF_DISCOVERY_ENABLED, False):
        discovery = DiscoveryPublisher(
            bridge,
            discovery_prefix=entry.data.get(CONF_DISCOVERY_PREFIX, "homeassistant"),
        )

    bridge.set_message_callback(handler.handle_message)

    _rebuild_maps(hass, exposure, resolver)

    await bridge.connect()
    await bridge.start_listening()

    await publisher.publish_all_states(hass)

    # Publish discovery if enabled
    if discovery:
        await discovery.publish_all(exposure.get_exposed_entities(), hass)

    async def _on_state_changed(event: Event) -> None:
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        if entity_id and new_state:
            await publisher.publish_state(entity_id, new_state)

    unsub_state = hass.bus.async_listen(EVENT_STATE_CHANGED, _on_state_changed)

    def _on_registry_changed(event: Event) -> None:
        _rebuild_maps(hass, exposure, resolver)

    unsub_device = hass.bus.async_listen("device_registry_updated", _on_registry_changed)
    unsub_entity = hass.bus.async_listen("entity_registry_updated", _on_registry_changed)

    entry.add_update_listener(_on_options_updated)

    hass.data[DOMAIN][entry.entry_id] = {
        "bridge": bridge,
        "resolver": resolver,
        "exposure": exposure,
        "publisher": publisher,
        "handler": handler,
        "discovery": discovery,
        "unsub_state": unsub_state,
        "unsub_device": unsub_device,
        "unsub_entity": unsub_entity,
    }

    _LOGGER.info("HA2MQTT integration loaded")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data:
        data["unsub_state"]()
        data["unsub_device"]()
        data["unsub_entity"]()
        if data.get("discovery"):
            await data["discovery"].remove_all(
                data["exposure"].get_exposed_entities()
            )
        await data["bridge"].disconnect()

    _LOGGER.info("HA2MQTT integration unloaded")
    return True


async def _on_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    data["exposure"].update_config(
        exposed_integrations=entry.options.get(CONF_EXPOSED_INTEGRATIONS, []),
        excluded_devices=entry.options.get(CONF_EXCLUDED_DEVICES, []),
    )
    _rebuild_maps(hass, data["exposure"], data["resolver"])
    await data["publisher"].publish_all_states(hass)


def _rebuild_maps(hass: HomeAssistant, exposure: ExposureManager, resolver: DeviceResolver) -> None:
    """Rebuild exposure and resolver maps from current registries."""
    if dr is None or er is None:
        return

    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)

    devices = {dev.id: dev for dev in device_reg.devices.values()}
    entities = list(entity_reg.entities.values())
    config_entries = {
        entry.entry_id: entry for entry in hass.config_entries.async_entries()
    }

    exposure.rebuild(devices, entities, config_entries)

    resolver._entity_map.clear()
    resolver._topic_to_entity.clear()
    resolver._device_slugs.clear()
    resolver._slug_counts.clear()

    for entity_id, info in exposure.get_exposed_entities().items():
        entity_key = _derive_entity_key(entity_id, info["device_name"])
        resolver.register_entity(
            entity_id=entity_id,
            integration=info["integration"],
            device_name=info["device_name"],
            domain=info["domain"],
            device_id=info["device_id"],
            entity_key=entity_key,
        )


def _derive_entity_key(entity_id: str, device_name: str) -> str:
    """Derive a meaningful key for an entity within its device.

    For entity_id 'sensor.living_room_thermostat_temperature' with
    device_name 'Living Room Thermostat', returns 'temperature'.
    For entity_id 'switch.living_room_thermostat' (matches device name),
    returns 'state'.
    """
    object_id = entity_id.split(".", 1)[1] if "." in entity_id else entity_id
    device_slug = slugify_name(device_name)

    # Strip device name prefix to get entity-specific part
    if object_id.startswith(device_slug + "_"):
        key = object_id[len(device_slug) + 1:]
        if key:
            return key

    # Entity object_id matches device slug exactly → primary entity
    if object_id == device_slug:
        return "state"

    # Fallback: use the full object_id
    return object_id
