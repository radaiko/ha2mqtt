"""Tests for the command handler."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha2mqtt.command_handler import CommandHandler


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.services = MagicMock()
    hass.services.async_call = AsyncMock()
    return hass


@pytest.fixture
def mock_resolver():
    resolver = MagicMock()
    return resolver


@pytest.fixture
def handler(mock_hass, mock_resolver):
    return CommandHandler(mock_hass, mock_resolver, topic_prefix="")


class TestCommandHandler:
    @pytest.mark.asyncio
    async def test_light_turn_on(self, handler, mock_hass, mock_resolver):
        # 4-segment: integration/domain/device/entity_key/set → attribute="state"
        mock_resolver.get_entity_id.return_value = "light.lamp"
        await handler.handle_message("homekit/light/lamp/state/set", "on")
        mock_hass.services.async_call.assert_called_once_with(
            "light", "turn_on", {"entity_id": "light.lamp"}
        )

    @pytest.mark.asyncio
    async def test_light_turn_off(self, handler, mock_hass, mock_resolver):
        mock_resolver.get_entity_id.return_value = "light.lamp"
        await handler.handle_message("homekit/light/lamp/state/set", "off")
        mock_hass.services.async_call.assert_called_once_with(
            "light", "turn_off", {"entity_id": "light.lamp"}
        )

    @pytest.mark.asyncio
    async def test_light_brightness(self, handler, mock_hass, mock_resolver):
        # 5-segment: integration/domain/device/entity_key/attribute/set
        mock_resolver.get_entity_id.return_value = "light.lamp"
        await handler.handle_message("homekit/light/lamp/state/brightness/set", "128")
        mock_hass.services.async_call.assert_called_once_with(
            "light", "turn_on", {"entity_id": "light.lamp", "brightness": 128}
        )

    @pytest.mark.asyncio
    async def test_climate_temperature(self, handler, mock_hass, mock_resolver):
        mock_resolver.get_entity_id.return_value = "climate.thermostat"
        await handler.handle_message("matter/climate/thermostat/state/temperature/set", "22.0")
        mock_hass.services.async_call.assert_called_once_with(
            "climate", "set_temperature", {"entity_id": "climate.thermostat", "temperature": 22.0}
        )

    @pytest.mark.asyncio
    async def test_cover_open(self, handler, mock_hass, mock_resolver):
        mock_resolver.get_entity_id.return_value = "cover.blinds"
        await handler.handle_message("hue/cover/blinds/state/set", "open")
        mock_hass.services.async_call.assert_called_once_with(
            "cover", "open_cover", {"entity_id": "cover.blinds"}
        )

    @pytest.mark.asyncio
    async def test_cover_position(self, handler, mock_hass, mock_resolver):
        mock_resolver.get_entity_id.return_value = "cover.blinds"
        await handler.handle_message("hue/cover/blinds/state/position/set", "50")
        mock_hass.services.async_call.assert_called_once_with(
            "cover", "set_cover_position", {"entity_id": "cover.blinds", "position": 50}
        )

    @pytest.mark.asyncio
    async def test_button_press(self, handler, mock_hass, mock_resolver):
        mock_resolver.get_entity_id.return_value = "button.doorbell"
        await handler.handle_message("matter/button/doorbell/state/set", "press")
        mock_hass.services.async_call.assert_called_once_with(
            "button", "press", {"entity_id": "button.doorbell"}
        )

    @pytest.mark.asyncio
    async def test_unknown_entity_ignored(self, handler, mock_hass, mock_resolver):
        mock_resolver.get_entity_id.return_value = None
        await handler.handle_message("hue/light/unknown/state/set", "on")
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_unknown_domain_ignored(self, handler, mock_hass, mock_resolver):
        mock_resolver.get_entity_id.return_value = "fake.entity"
        await handler.handle_message("hue/fake_domain/thing/state/set", "on")
        mock_hass.services.async_call.assert_not_called()

    @pytest.mark.asyncio
    async def test_topic_with_prefix(self, mock_hass, mock_resolver):
        handler = CommandHandler(mock_hass, mock_resolver, topic_prefix="myprefix")
        mock_resolver.get_entity_id.return_value = "light.lamp"
        await handler.handle_message("myprefix/homekit/light/lamp/state/set", "on")
        mock_hass.services.async_call.assert_called_once_with(
            "light", "turn_on", {"entity_id": "light.lamp"}
        )
