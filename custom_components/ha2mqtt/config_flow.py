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

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

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


async def test_mqtt_connection(
    host: str, port: int, username: str | None, password: str | None, tls: bool
) -> bool:
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
    except Exception:  # noqa: BLE001
        return False


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BROKER_HOST, default=DEFAULT_BROKER_HOST): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Required(CONF_BROKER_PORT, default=DEFAULT_BROKER_PORT): NumberSelector(
            NumberSelectorConfig(min=1, max=65535, mode=NumberSelectorMode.BOX)
        ),
        vol.Optional(CONF_BROKER_USERNAME, default=""): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Optional(CONF_BROKER_PASSWORD, default=""): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_BROKER_TLS, default=DEFAULT_BROKER_TLS): BooleanSelector(),
        vol.Optional(CONF_TOPIC_PREFIX, default=DEFAULT_TOPIC_PREFIX): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT)
        ),
        vol.Optional(
            CONF_DISCOVERY_ENABLED, default=DEFAULT_DISCOVERY_ENABLED
        ): BooleanSelector(),
        vol.Optional(
            CONF_DISCOVERY_PREFIX, default=DEFAULT_DISCOVERY_PREFIX
        ): TextSelector(TextSelectorConfig(type=TextSelectorType.TEXT)),
        vol.Optional(CONF_RETAIN, default=DEFAULT_RETAIN): BooleanSelector(),
        vol.Optional(CONF_QOS, default=DEFAULT_QOS): SelectSelector(
            SelectSelectorConfig(
                options=[
                    {"value": "0", "label": "0 – At most once (fire and forget)"},
                    {"value": "1", "label": "1 – At least once (acknowledged)"},
                    {"value": "2", "label": "2 – Exactly once (guaranteed)"},
                ],
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
    }
)


class Ha2MqttConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA2MQTT."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._user_config: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Step 1: MQTT broker + feature configuration."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # SelectSelector returns strings — coerce QoS back to int
            user_input[CONF_QOS] = int(user_input.get(CONF_QOS, 0))
            # NumberSelector may return float — coerce port to int
            user_input[CONF_BROKER_PORT] = int(user_input.get(CONF_BROKER_PORT, DEFAULT_BROKER_PORT))

            connected = await test_mqtt_connection(
                host=user_input[CONF_BROKER_HOST],
                port=user_input[CONF_BROKER_PORT],
                username=user_input.get(CONF_BROKER_USERNAME),
                password=user_input.get(CONF_BROKER_PASSWORD),
                tls=user_input.get(CONF_BROKER_TLS, False),
            )

            if connected:
                self._user_config = user_input
                return await self.async_step_integrations()

            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_integrations(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Step 2: Select integrations to expose."""
        if user_input is not None:
            data = {**self._user_config}
            options = {
                CONF_EXPOSED_INTEGRATIONS: user_input.get(
                    CONF_EXPOSED_INTEGRATIONS, []
                ),
                CONF_EXCLUDED_DEVICES: [],
            }
            return self.async_create_entry(
                title="HA2MQTT",
                data=data,
                options=options,
            )

        integrations: set[str] = set()
        if self.hass:
            for entry in self.hass.config_entries.async_entries():
                integrations.add(entry.domain)
        integration_options = {domain: domain for domain in sorted(integrations)}

        schema = vol.Schema(
            {
                vol.Required(CONF_EXPOSED_INTEGRATIONS): cv.multi_select(
                    integration_options
                ),
            }
        )

        return self.async_show_form(step_id="integrations", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> Ha2MqttOptionsFlow:
        """Get the options flow handler."""
        return Ha2MqttOptionsFlow()


class Ha2MqttOptionsFlow(OptionsFlow):
    """Handle options flow for HA2MQTT."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Handle options flow."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self.config_entry.options

        # Build dynamic integration list for cv.multi_select
        integrations: set[str] = set()
        for entry in self.hass.config_entries.async_entries():
            integrations.add(entry.domain)
        integration_options = {domain: domain for domain in sorted(integrations)}

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_EXPOSED_INTEGRATIONS,
                    default=current.get(CONF_EXPOSED_INTEGRATIONS, []),
                ): cv.multi_select(integration_options),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
