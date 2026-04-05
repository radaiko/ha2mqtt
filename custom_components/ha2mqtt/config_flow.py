"""Config flow for HA2MQTT."""

from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any

try:
    import aiomqtt
except ImportError:
    aiomqtt = None

try:
    import voluptuous as vol
    from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
    from homeassistant.core import callback
    from homeassistant.data_entry_flow import FlowResult
except ImportError:
    # For testing without HA installed
    ConfigFlow = object
    OptionsFlow = object
    ConfigEntry = object
    FlowResult = dict
    callback = lambda f: f
    vol = None

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
    DEFAULT_BROKER_HOST,
    DEFAULT_BROKER_PORT,
    DEFAULT_BROKER_TLS,
    DEFAULT_DISCOVERY_ENABLED,
    DEFAULT_DISCOVERY_PREFIX,
    DEFAULT_QOS,
    DEFAULT_RETAIN,
    DEFAULT_TOPIC_PREFIX,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def test_mqtt_connection(host: str, port: int, username: str | None, password: str | None, tls: bool) -> bool:
    """Test if we can connect to the MQTT broker."""
    try:
        tls_params = ssl.create_default_context() if tls else None
        client = aiomqtt.Client(
            hostname=host,
            port=port,
            username=username or None,
            password=password or None,
            tls_params=tls_params,
        )
        async with client:
            pass
        return True
    except (aiomqtt.MqttError, OSError, asyncio.TimeoutError):
        return False


class Ha2MqttConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA2MQTT."""

    VERSION = 1

    def __init__(self) -> None:
        self._broker_config: dict[str, Any] = {}
        self._features_config: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 1: MQTT broker configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            connected = await test_mqtt_connection(
                host=user_input[CONF_BROKER_HOST],
                port=user_input[CONF_BROKER_PORT],
                username=user_input.get(CONF_BROKER_USERNAME),
                password=user_input.get(CONF_BROKER_PASSWORD),
                tls=user_input.get(CONF_BROKER_TLS, False),
            )

            if connected:
                self._broker_config = user_input
                return await self.async_step_features()

            errors["base"] = "cannot_connect"

        schema = vol.Schema(
            {
                vol.Required(CONF_BROKER_HOST, default=DEFAULT_BROKER_HOST): str,
                vol.Required(CONF_BROKER_PORT, default=DEFAULT_BROKER_PORT): int,
                vol.Optional(CONF_BROKER_USERNAME, default=""): str,
                vol.Optional(CONF_BROKER_PASSWORD, default=""): str,
                vol.Optional(CONF_BROKER_TLS, default=DEFAULT_BROKER_TLS): bool,
                vol.Optional(CONF_TOPIC_PREFIX, default=DEFAULT_TOPIC_PREFIX): str,
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_features(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 2: Feature toggles."""
        if user_input is not None:
            self._features_config = user_input
            return await self.async_step_integrations()

        schema = vol.Schema(
            {
                vol.Optional(CONF_DISCOVERY_ENABLED, default=DEFAULT_DISCOVERY_ENABLED): bool,
                vol.Optional(CONF_DISCOVERY_PREFIX, default=DEFAULT_DISCOVERY_PREFIX): str,
                vol.Optional(CONF_RETAIN, default=DEFAULT_RETAIN): bool,
                vol.Optional(CONF_QOS, default=DEFAULT_QOS): vol.In([0, 1, 2]),
            }
        )

        return self.async_show_form(step_id="features", data_schema=schema)

    async def async_step_integrations(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step 3: Select integrations to expose."""
        if user_input is not None:
            data = {**self._broker_config, **self._features_config}
            options = {
                CONF_EXPOSED_INTEGRATIONS: user_input.get(CONF_EXPOSED_INTEGRATIONS, []),
                CONF_EXCLUDED_DEVICES: [],
            }
            return self.async_create_entry(
                title="HA2MQTT",
                data=data,
                options=options,
            )

        integrations = set()
        if self.hass:
            for entry in self.hass.config_entries.async_entries():
                integrations.add(entry.domain)
        integration_list = sorted(integrations)

        schema = vol.Schema(
            {
                vol.Required(CONF_EXPOSED_INTEGRATIONS): vol.All(
                    [vol.In(integration_list)] if integration_list else [str]
                ),
            }
        )

        return self.async_show_form(step_id="integrations", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> Ha2MqttOptionsFlow:
        return Ha2MqttOptionsFlow(config_entry)


class Ha2MqttOptionsFlow(OptionsFlow):
    """Handle options flow for HA2MQTT."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    CONF_EXPOSED_INTEGRATIONS,
                    default=current.get(CONF_EXPOSED_INTEGRATIONS, []),
                ): list,
                vol.Optional(
                    CONF_EXCLUDED_DEVICES,
                    default=current.get(CONF_EXCLUDED_DEVICES, []),
                ): list,
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
