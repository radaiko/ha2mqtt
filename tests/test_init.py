"""Tests for the HA2MQTT integration setup."""

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock homeassistant modules before importing
sys.modules.setdefault("homeassistant", MagicMock())
sys.modules.setdefault("homeassistant.config_entries", MagicMock())
sys.modules.setdefault("homeassistant.const", MagicMock(EVENT_STATE_CHANGED="state_changed"))
sys.modules.setdefault("homeassistant.core", MagicMock())
sys.modules.setdefault("homeassistant.helpers", MagicMock())
sys.modules.setdefault("homeassistant.helpers.device_registry", MagicMock())
sys.modules.setdefault("homeassistant.helpers.entity_registry", MagicMock())

from custom_components.ha2mqtt.const import DOMAIN


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.data = {}
    hass.bus = MagicMock()
    hass.bus.async_listen = MagicMock(return_value=MagicMock())
    hass.states = MagicMock()
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries.return_value = []
    return hass


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        "broker_host": "localhost",
        "broker_port": 1883,
        "broker_username": "",
        "broker_password": "",
        "broker_tls": False,
        "topic_prefix": "",
    }
    entry.options = {
        "discovery_enabled": False,
        "discovery_prefix": "homeassistant",
        "retain": True,
        "qos": 0,
        "exposed_integrations": ["hue"],
        "excluded_devices": [],
    }
    entry.add_update_listener = MagicMock()
    return entry


class TestSetup:
    @pytest.mark.asyncio
    async def test_setup_entry_stores_runtime_data(self, mock_hass, mock_entry):
        with patch("custom_components.ha2mqtt.MQTTBridge") as mock_bridge_cls, \
             patch("custom_components.ha2mqtt.DeviceResolver"), \
             patch("custom_components.ha2mqtt.ExposureManager"), \
             patch("custom_components.ha2mqtt.StatePublisher") as mock_publisher_cls, \
             patch("custom_components.ha2mqtt.CommandHandler"), \
             patch("custom_components.ha2mqtt._rebuild_maps"):

            mock_bridge = AsyncMock()
            mock_bridge.connected = True
            mock_bridge_cls.return_value = mock_bridge

            mock_publisher = AsyncMock()
            mock_publisher_cls.return_value = mock_publisher

            from custom_components.ha2mqtt import async_setup_entry
            result = await async_setup_entry(mock_hass, mock_entry)

        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_entry.entry_id in mock_hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_entry_disconnects(self, mock_hass, mock_entry):
        mock_bridge = AsyncMock()
        mock_hass.data = {
            DOMAIN: {
                mock_entry.entry_id: {
                    "bridge": mock_bridge,
                    "unsub_state": MagicMock(),
                    "unsub_device": MagicMock(),
                    "unsub_entity": MagicMock(),
                }
            }
        }

        from custom_components.ha2mqtt import async_unload_entry
        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        mock_bridge.disconnect.assert_called_once()
