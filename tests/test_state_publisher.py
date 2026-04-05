"""Tests for the state publisher."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha2mqtt.state_publisher import StatePublisher


@pytest.fixture
def mock_bridge():
    bridge = MagicMock()
    bridge.build_topic = MagicMock(side_effect=lambda *args: "/".join(args))
    bridge.publish = AsyncMock()
    return bridge


@pytest.fixture
def mock_resolver():
    resolver = MagicMock()
    return resolver


@pytest.fixture
def mock_exposure():
    exposure = MagicMock()
    return exposure


@pytest.fixture
def publisher(mock_bridge, mock_resolver, mock_exposure):
    return StatePublisher(mock_bridge, mock_resolver, mock_exposure)


class TestStatePublisher:
    @pytest.mark.asyncio
    async def test_publish_state_for_exposed_entity(self, publisher, mock_resolver, mock_exposure):
        mock_exposure.is_exposed.return_value = True
        mock_resolver.resolve.return_value = {
            "integration": "hue",
            "device_class": "light",
            "device_name": "lamp",
            "entity_key": "state",
        }

        state = MagicMock()
        state.state = "on"
        state.attributes = {"brightness": 255, "color_temp": 400}

        await publisher.publish_state("light.lamp", state)

        assert mock_resolver.resolve.called
        # state + 2 attributes = 3 publishes
        assert publisher._bridge.publish.call_count == 3

    @pytest.mark.asyncio
    async def test_skip_unexposed_entity(self, publisher, mock_exposure):
        mock_exposure.is_exposed.return_value = False

        state = MagicMock()
        state.state = "on"
        state.attributes = {}

        await publisher.publish_state("light.other", state)

        assert publisher._bridge.publish.call_count == 0

    @pytest.mark.asyncio
    async def test_publish_attributes_under_entity_key(self, publisher, mock_bridge, mock_resolver, mock_exposure):
        """Attributes are published under entity_key/attr_name."""
        mock_exposure.is_exposed.return_value = True
        mock_resolver.resolve.return_value = {
            "integration": "hk",
            "device_class": "sensor",
            "device_name": "motion",
            "entity_key": "temperature",
        }

        state = MagicMock()
        state.state = "22.5"
        state.attributes = {"unit_of_measurement": "°C"}

        await publisher.publish_state("sensor.motion_temp", state)

        calls = mock_bridge.publish.call_args_list
        assert len(calls) == 2
        # State value: hk/sensor/motion/temperature
        assert calls[0][0][0] == "hk/sensor/motion/temperature"
        assert calls[0][0][1] == "22.5"
        # Attribute: hk/sensor/motion/temperature/unit_of_measurement
        assert calls[1][0][0] == "hk/sensor/motion/temperature/unit_of_measurement"
        assert calls[1][0][1] == "°C"

    @pytest.mark.asyncio
    async def test_skip_internal_attributes(self, publisher, mock_bridge, mock_resolver, mock_exposure):
        mock_exposure.is_exposed.return_value = True
        mock_resolver.resolve.return_value = {
            "integration": "hue",
            "device_class": "light",
            "device_name": "lamp",
            "entity_key": "state",
        }

        state = MagicMock()
        state.state = "on"
        state.attributes = {
            "brightness": 200,
            "friendly_name": "Lamp",
            "supported_features": 44,
            "entity_picture": "/local/img.png",
            "icon": "mdi:lightbulb",
        }

        await publisher.publish_state("light.lamp", state)

        topics_published = [call[0][0] for call in mock_bridge.publish.call_args_list]
        assert "hue/light/lamp/state" in topics_published
        assert "hue/light/lamp/state/brightness" in topics_published
        assert "hue/light/lamp/state/friendly_name" not in topics_published
        assert "hue/light/lamp/state/supported_features" not in topics_published
