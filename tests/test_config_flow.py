"""Tests for the config flow."""

from unittest.mock import AsyncMock, MagicMock, patch
import sys
import types

import pytest


# Build stub HA modules with real base classes so Ha2MqttConfigFlow inherits properly
class _StubConfigFlow:
    """Stub base class for ConfigFlow."""
    def __init_subclass__(cls, domain=None, **kwargs):
        super().__init_subclass__(**kwargs)


class _StubOptionsFlow:
    """Stub base class for OptionsFlow."""


_config_entries_mod = types.ModuleType("homeassistant.config_entries")
_config_entries_mod.ConfigFlow = _StubConfigFlow
_config_entries_mod.OptionsFlow = _StubOptionsFlow
_config_entries_mod.ConfigEntry = object

_core_mod = types.ModuleType("homeassistant.core")
_core_mod.callback = lambda f: f

_data_entry_flow_mod = types.ModuleType("homeassistant.data_entry_flow")
_data_entry_flow_mod.FlowResult = dict

_ha_mod = types.ModuleType("homeassistant")

sys.modules.setdefault("homeassistant", _ha_mod)
sys.modules.setdefault("homeassistant.config_entries", _config_entries_mod)
sys.modules.setdefault("homeassistant.core", _core_mod)
sys.modules.setdefault("homeassistant.data_entry_flow", _data_entry_flow_mod)
sys.modules.setdefault("homeassistant.helpers", types.ModuleType("homeassistant.helpers"))
sys.modules.setdefault("homeassistant.helpers.config_entry_flow", types.ModuleType("homeassistant.helpers.config_entry_flow"))
sys.modules.setdefault("voluptuous", MagicMock())

from custom_components.ha2mqtt.config_flow import Ha2MqttConfigFlow
from custom_components.ha2mqtt.const import DOMAIN


class TestConfigFlow:
    @pytest.mark.asyncio
    async def test_step_user_shows_broker_form(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config_entries = MagicMock()
        flow.hass.config_entries.async_entries.return_value = []
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "user"})

        result = await flow.async_step_user(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_step_user_with_valid_broker(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config_entries = MagicMock()
        flow.hass.config_entries.async_entries.return_value = []
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "features"})

        with patch(
            "custom_components.ha2mqtt.config_flow.test_mqtt_connection",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await flow.async_step_user(
                user_input={
                    "broker_host": "localhost",
                    "broker_port": 1883,
                    "broker_username": "",
                    "broker_password": "",
                    "broker_tls": False,
                    "topic_prefix": "",
                }
            )

        assert result["type"] == "form"
        assert result["step_id"] == "features"

    @pytest.mark.asyncio
    async def test_step_user_with_invalid_broker(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config_entries = MagicMock()
        flow.hass.config_entries.async_entries.return_value = []
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "user", "errors": {"base": "cannot_connect"}})

        with patch(
            "custom_components.ha2mqtt.config_flow.test_mqtt_connection",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await flow.async_step_user(
                user_input={
                    "broker_host": "badhost",
                    "broker_port": 1883,
                    "broker_username": "",
                    "broker_password": "",
                    "broker_tls": False,
                    "topic_prefix": "",
                }
            )

        assert result["type"] == "form"
        # The flow calls async_show_form with errors, check that was called correctly
        flow.async_show_form.assert_called_once()
        call_kwargs = flow.async_show_form.call_args
        assert call_kwargs[1]["errors"]["base"] == "cannot_connect" or call_kwargs.kwargs["errors"]["base"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_step_features_advances_to_integrations(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow._broker_config = {"broker_host": "localhost", "broker_port": 1883}
        flow.async_show_form = MagicMock(return_value={"type": "form", "step_id": "integrations"})

        result = await flow.async_step_features(
            user_input={
                "discovery_enabled": False,
                "discovery_prefix": "homeassistant",
                "retain": True,
                "qos": 0,
            }
        )

        assert result["type"] == "form"
        assert result["step_id"] == "integrations"

    @pytest.mark.asyncio
    async def test_step_integrations_creates_entry(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow._broker_config = {
            "broker_host": "localhost",
            "broker_port": 1883,
            "broker_username": "",
            "broker_password": "",
            "broker_tls": False,
            "topic_prefix": "",
        }
        flow._features_config = {
            "discovery_enabled": False,
            "discovery_prefix": "homeassistant",
            "retain": True,
            "qos": 0,
        }

        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        result = await flow.async_step_integrations(
            user_input={"exposed_integrations": ["hue", "matter"]}
        )

        assert result["type"] == "create_entry"
