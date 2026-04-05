"""Tests for ha2mqtt constants."""

from custom_components.ha2mqtt.const import (
    DOMAIN,
    SERVICE_MAP,
    DEFAULT_BROKER_HOST,
    DEFAULT_BROKER_PORT,
)


def test_domain():
    assert DOMAIN == "ha2mqtt"


def test_service_map_has_required_domains():
    required = {"light", "switch", "climate", "fan", "cover", "number", "select", "button", "lock", "media_player"}
    assert required.issubset(set(SERVICE_MAP.keys()))


def test_service_map_light_has_state():
    assert "state" in SERVICE_MAP["light"]
    assert "on" in SERVICE_MAP["light"]["state"]
    assert "off" in SERVICE_MAP["light"]["state"]


def test_defaults():
    assert DEFAULT_BROKER_HOST == "localhost"
    assert DEFAULT_BROKER_PORT == 1883
