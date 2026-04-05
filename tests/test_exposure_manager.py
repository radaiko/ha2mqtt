"""Tests for the exposure manager."""

from unittest.mock import MagicMock

import pytest

from custom_components.ha2mqtt.exposure_manager import ExposureManager


def _make_device(device_id, name, integration):
    """Create a mock device registry entry."""
    device = MagicMock()
    device.id = device_id
    device.name = name
    device.name_by_user = None
    device.config_entries = {f"entry_{integration}"}
    return device


def _make_entity(entity_id, domain, device_id, platform):
    """Create a mock entity registry entry."""
    entity = MagicMock()
    entity.entity_id = entity_id
    entity.domain = domain
    entity.device_id = device_id
    entity.platform = platform
    entity.disabled = False
    return entity


def _make_config_entry(entry_id, domain):
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = entry_id
    entry.domain = domain
    return entry


class TestExposureManager:
    def test_entity_exposed_when_integration_selected(self):
        manager = ExposureManager(exposed_integrations=["hue"], excluded_devices=[])
        devices = {"dev1": _make_device("dev1", "Lamp", "hue")}
        entities = [_make_entity("light.lamp", "light", "dev1", "hue")]
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}
        manager.rebuild(devices, entities, config_entries)
        assert manager.is_exposed("light.lamp") is True

    def test_entity_not_exposed_when_integration_not_selected(self):
        manager = ExposureManager(exposed_integrations=["hue"], excluded_devices=[])
        devices = {"dev1": _make_device("dev1", "Switch", "zwave")}
        entities = [_make_entity("switch.z", "switch", "dev1", "zwave")]
        config_entries = {"entry_zwave": _make_config_entry("entry_zwave", "zwave")}
        manager.rebuild(devices, entities, config_entries)
        assert manager.is_exposed("switch.z") is False

    def test_device_excluded_overrides_integration(self):
        manager = ExposureManager(exposed_integrations=["hue"], excluded_devices=["dev1"])
        devices = {"dev1": _make_device("dev1", "Lamp", "hue")}
        entities = [_make_entity("light.lamp", "light", "dev1", "hue")]
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}
        manager.rebuild(devices, entities, config_entries)
        assert manager.is_exposed("light.lamp") is False

    def test_entity_without_device_not_exposed(self):
        manager = ExposureManager(exposed_integrations=["hue"], excluded_devices=[])
        entities = [_make_entity("sensor.standalone", "sensor", None, "hue")]
        manager.rebuild({}, entities, {})
        assert manager.is_exposed("sensor.standalone") is False

    def test_disabled_entity_not_exposed(self):
        manager = ExposureManager(exposed_integrations=["hue"], excluded_devices=[])
        devices = {"dev1": _make_device("dev1", "Lamp", "hue")}
        entity = _make_entity("light.lamp", "light", "dev1", "hue")
        entity.disabled = True
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}
        manager.rebuild(devices, entities=[entity], config_entries=config_entries)
        assert manager.is_exposed("light.lamp") is False

    def test_get_exposed_entities(self):
        manager = ExposureManager(exposed_integrations=["hue"], excluded_devices=[])
        devices = {"dev1": _make_device("dev1", "Lamp", "hue"), "dev2": _make_device("dev2", "Sensor", "hue")}
        entities = [_make_entity("light.lamp", "light", "dev1", "hue"), _make_entity("sensor.temp", "sensor", "dev2", "hue")]
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}
        manager.rebuild(devices, entities, config_entries)
        exposed = manager.get_exposed_entities()
        assert len(exposed) == 2

    def test_get_entity_info(self):
        manager = ExposureManager(exposed_integrations=["hue"], excluded_devices=[])
        devices = {"dev1": _make_device("dev1", "Lamp", "hue")}
        entities = [_make_entity("light.lamp", "light", "dev1", "hue")]
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}
        manager.rebuild(devices, entities, config_entries)
        info = manager.get_entity_info("light.lamp")
        assert info["integration"] == "hue"
        assert info["device_name"] == "Lamp"
        assert info["domain"] == "light"
