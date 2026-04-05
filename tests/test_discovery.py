"""Tests for the MQTT discovery publisher."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha2mqtt.discovery import DiscoveryPublisher


@pytest.fixture
def mock_bridge():
    bridge = MagicMock()
    bridge.publish = AsyncMock()
    bridge.availability_topic = "ha2mqtt/status"
    bridge.build_topic = MagicMock(side_effect=lambda i, d, n, a: f"{i}/{d}/{n}/{a}")
    return bridge


@pytest.fixture
def publisher(mock_bridge):
    return DiscoveryPublisher(mock_bridge, discovery_prefix="homeassistant")


class TestDiscoveryPublisher:
    @pytest.mark.asyncio
    async def test_publish_light_discovery(self, publisher, mock_bridge):
        await publisher.publish_discovery(
            entity_id="light.lamp",
            integration="hue",
            device_class="light",
            device_name="lamp",
            attributes=["state", "brightness", "color_temp"],
        )

        assert mock_bridge.publish.called
        call_args = mock_bridge.publish.call_args_list[0]
        topic = call_args[0][0]
        payload = json.loads(call_args[0][1])

        assert topic == "homeassistant/light/ha2mqtt_light_lamp/config"
        assert payload["name"] == "lamp"
        assert "state_topic" in payload
        assert "command_topic" in payload
        assert payload["availability_topic"] == "ha2mqtt/status"

    @pytest.mark.asyncio
    async def test_publish_sensor_discovery_no_command(self, publisher, mock_bridge):
        await publisher.publish_discovery(
            entity_id="sensor.temp",
            integration="matter",
            device_class="sensor",
            device_name="temp",
            attributes=["state"],
        )

        call_args = mock_bridge.publish.call_args_list[0]
        payload = json.loads(call_args[0][1])

        assert "state_topic" in payload
        assert "command_topic" not in payload

    @pytest.mark.asyncio
    async def test_remove_discovery(self, publisher, mock_bridge):
        await publisher.remove_discovery("light", "light.lamp")

        mock_bridge.publish.assert_called_once()
        call_args = mock_bridge.publish.call_args
        assert call_args[0][1] == ""  # Empty payload removes discovery
        assert call_args[1]["retain"] is True
