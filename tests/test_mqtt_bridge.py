"""Tests for the MQTT bridge."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ha2mqtt.mqtt_bridge import MQTTBridge
from custom_components.ha2mqtt.const import (
    PAYLOAD_ONLINE,
    PAYLOAD_OFFLINE,
    AVAILABILITY_TOPIC_SUFFIX,
)


@pytest.fixture
def bridge_config():
    return {
        "host": "localhost",
        "port": 1883,
        "username": None,
        "password": None,
        "tls": False,
        "topic_prefix": "",
        "retain": True,
        "qos": 0,
    }


@pytest.fixture
def bridge(bridge_config):
    return MQTTBridge(bridge_config)


def test_bridge_init(bridge):
    assert bridge.host == "localhost"
    assert bridge.port == 1883
    assert bridge.connected is False


def test_build_topic_no_prefix(bridge):
    result = bridge.build_topic("homekit", "light", "lamp", "state")
    assert result == "homekit/light/lamp/state"


def test_build_topic_with_prefix():
    config = {
        "host": "localhost",
        "port": 1883,
        "username": None,
        "password": None,
        "tls": False,
        "topic_prefix": "myprefix",
        "retain": True,
        "qos": 0,
    }
    bridge = MQTTBridge(config)
    result = bridge.build_topic("homekit", "light", "lamp", "state")
    assert result == "myprefix/homekit/light/lamp/state"


def test_availability_topic_no_prefix(bridge):
    assert bridge.availability_topic == "ha2mqtt/status"


def test_availability_topic_with_prefix():
    config = {
        "host": "localhost",
        "port": 1883,
        "username": None,
        "password": None,
        "tls": False,
        "topic_prefix": "myprefix",
        "retain": True,
        "qos": 0,
    }
    bridge = MQTTBridge(config)
    assert bridge.availability_topic == "myprefix/ha2mqtt/status"


def test_set_topic(bridge):
    result = bridge.build_set_topic("homekit", "light", "lamp", "state", "brightness")
    assert result == "homekit/light/lamp/state/brightness/set"


def test_build_topic_variable_segments(bridge):
    # 4 segments (entity state)
    assert bridge.build_topic("hk", "sensor", "motion", "temperature") == "hk/sensor/motion/temperature"
    # 5 segments (entity attribute)
    assert bridge.build_topic("hk", "sensor", "motion", "temperature", "unit") == "hk/sensor/motion/temperature/unit"
