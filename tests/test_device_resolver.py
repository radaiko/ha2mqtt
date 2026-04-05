"""Tests for the device resolver."""

import pytest

from custom_components.ha2mqtt.device_resolver import DeviceResolver, slugify_name


def test_slugify_name_basic():
    assert slugify_name("Living Room Lamp") == "living_room_lamp"


def test_slugify_name_special_chars():
    assert slugify_name("Küchen-Licht (1)") == "kuchen_licht_1"


def test_slugify_name_multiple_spaces():
    assert slugify_name("my   device   name") == "my_device_name"


def test_slugify_name_trailing():
    assert slugify_name("  test  ") == "test"


class TestDeviceResolver:
    """Tests for the DeviceResolver class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.resolver = DeviceResolver()

    def test_resolve_topic_parts(self):
        self.resolver.register_entity(
            entity_id="light.living_room",
            integration="homekit_controller",
            device_name="Living Room Lamp",
            domain="light",
        )
        parts = self.resolver.resolve("light.living_room")
        assert parts == {
            "integration": "homekit_controller",
            "device_class": "light",
            "device_name": "living_room_lamp",
        }

    def test_resolve_unknown_entity(self):
        result = self.resolver.resolve("light.unknown")
        assert result is None

    def test_duplicate_device_names_get_suffix(self):
        self.resolver.register_entity(
            entity_id="light.lamp_a",
            integration="hue",
            device_name="Lamp",
            domain="light",
        )
        self.resolver.register_entity(
            entity_id="light.lamp_b",
            integration="hue",
            device_name="Lamp",
            domain="light",
        )
        parts_a = self.resolver.resolve("light.lamp_a")
        parts_b = self.resolver.resolve("light.lamp_b")
        assert parts_a["device_name"] == "lamp"
        assert parts_b["device_name"] == "lamp_2"

    def test_get_entity_id_from_topic_parts(self):
        self.resolver.register_entity(
            entity_id="light.living_room",
            integration="homekit_controller",
            device_name="Living Room Lamp",
            domain="light",
        )
        entity_id = self.resolver.get_entity_id("homekit_controller", "light", "living_room_lamp")
        assert entity_id == "light.living_room"

    def test_get_entity_id_not_found(self):
        result = self.resolver.get_entity_id("hue", "light", "nonexistent")
        assert result is None

    def test_get_all_entities(self):
        self.resolver.register_entity(
            entity_id="light.a",
            integration="hue",
            device_name="A",
            domain="light",
        )
        self.resolver.register_entity(
            entity_id="sensor.b",
            integration="hue",
            device_name="B",
            domain="sensor",
        )
        entities = self.resolver.get_all_entity_ids()
        assert set(entities) == {"light.a", "sensor.b"}

    def test_unregister_entity(self):
        self.resolver.register_entity(
            entity_id="light.a",
            integration="hue",
            device_name="A",
            domain="light",
        )
        self.resolver.unregister_entity("light.a")
        assert self.resolver.resolve("light.a") is None
