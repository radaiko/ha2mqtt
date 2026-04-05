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
            device_id="dev1",
            entity_key="state",
        )
        parts = self.resolver.resolve("light.living_room")
        assert parts == {
            "integration": "homekit_controller",
            "device_class": "light",
            "device_name": "living_room_lamp",
            "entity_key": "state",
        }

    def test_resolve_unknown_entity(self):
        result = self.resolver.resolve("light.unknown")
        assert result is None

    def test_same_device_entities_share_slug(self):
        """Multiple entities of the same physical device share one device slug."""
        self.resolver.register_entity("sensor.motion_lux", "hk", "Motion Sensor", "sensor", "dev1", "illuminance")
        self.resolver.register_entity("sensor.motion_temp", "hk", "Motion Sensor", "sensor", "dev1", "temperature")
        self.resolver.register_entity("sensor.motion_hum", "hk", "Motion Sensor", "sensor", "dev1", "humidity")

        p1 = self.resolver.resolve("sensor.motion_lux")
        p2 = self.resolver.resolve("sensor.motion_temp")
        p3 = self.resolver.resolve("sensor.motion_hum")

        assert p1["device_name"] == "motion_sensor"
        assert p2["device_name"] == "motion_sensor"
        assert p3["device_name"] == "motion_sensor"

        assert p1["entity_key"] == "illuminance"
        assert p2["entity_key"] == "temperature"
        assert p3["entity_key"] == "humidity"

    def test_different_devices_same_name_get_suffix(self):
        """Different physical devices with the same name get suffixed."""
        self.resolver.register_entity("light.lamp_a", "hue", "Lamp", "light", "dev1", "state")
        self.resolver.register_entity("light.lamp_b", "hue", "Lamp", "light", "dev2", "state")

        parts_a = self.resolver.resolve("light.lamp_a")
        parts_b = self.resolver.resolve("light.lamp_b")
        assert parts_a["device_name"] == "lamp"
        assert parts_b["device_name"] == "lamp_2"

    def test_get_entity_id_from_topic_parts(self):
        self.resolver.register_entity(
            "light.living_room", "homekit_controller", "Living Room Lamp", "light", "dev1", "state"
        )
        entity_id = self.resolver.get_entity_id("homekit_controller", "light", "living_room_lamp", "state")
        assert entity_id == "light.living_room"

    def test_get_entity_id_not_found(self):
        result = self.resolver.get_entity_id("hue", "light", "nonexistent", "state")
        assert result is None

    def test_get_all_entities(self):
        self.resolver.register_entity("light.a", "hue", "A", "light", "dev1", "state")
        self.resolver.register_entity("sensor.b", "hue", "B", "sensor", "dev2", "state")
        entities = self.resolver.get_all_entity_ids()
        assert set(entities) == {"light.a", "sensor.b"}

    def test_unregister_entity(self):
        self.resolver.register_entity("light.a", "hue", "A", "light", "dev1", "state")
        self.resolver.unregister_entity("light.a")
        assert self.resolver.resolve("light.a") is None
        assert self.resolver.get_entity_id("hue", "light", "a", "state") is None

    def test_cross_domain_same_device(self):
        """Entities in different domains but same device share the slug."""
        self.resolver.register_entity("sensor.motion_temp", "hk", "Motion", "sensor", "dev1", "temperature")
        self.resolver.register_entity("binary_sensor.motion", "hk", "Motion", "binary_sensor", "dev1", "state")

        p1 = self.resolver.resolve("sensor.motion_temp")
        p2 = self.resolver.resolve("binary_sensor.motion")

        assert p1["device_name"] == "motion"
        assert p2["device_name"] == "motion"
