"""The HA2MQTT integration."""

from .const import DOMAIN


async def async_setup_entry(hass, entry):
    """Set up HA2MQTT from a config entry."""
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    return True
