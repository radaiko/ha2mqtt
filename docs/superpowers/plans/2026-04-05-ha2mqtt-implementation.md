# HA2MQTT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a HACS custom integration that bridges HA entities to MQTT bidirectionally, organized by source integration.

**Architecture:** Event-listener architecture using HA's event bus for real-time state changes. Independent aiomqtt connection to MQTT broker. Domain-based service mapping for bidirectional control.

**Tech Stack:** Python 3.12+, Home Assistant 2024.1+, aiomqtt 2.x, HACS

---

### Task 1: Project Scaffold & Constants

**Files:**
- Create: `custom_components/ha2mqtt/__init__.py`
- Create: `custom_components/ha2mqtt/manifest.json`
- Create: `custom_components/ha2mqtt/const.py`
- Create: `hacs.json`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_const.py`

- [ ] **Step 1: Create manifest.json**

```json
{
  "domain": "ha2mqtt",
  "name": "HA2MQTT",
  "codeowners": ["@radaiko"],
  "config_flow": true,
  "dependencies": [],
  "documentation": "https://github.com/radaiko/ha2mqtt",
  "iot_class": "local_push",
  "issue_tracker": "https://github.com/radaiko/ha2mqtt/issues",
  "requirements": ["aiomqtt>=2.0.0"],
  "version": "0.1.0"
}
```

- [ ] **Step 2: Create hacs.json**

```json
{
  "name": "HA2MQTT",
  "render_readme": true,
  "homeassistant": "2024.1.0"
}
```

- [ ] **Step 3: Create const.py**

```python
"""Constants for the HA2MQTT integration."""

DOMAIN = "ha2mqtt"

# Config keys
CONF_BROKER_HOST = "broker_host"
CONF_BROKER_PORT = "broker_port"
CONF_BROKER_USERNAME = "broker_username"
CONF_BROKER_PASSWORD = "broker_password"
CONF_BROKER_TLS = "broker_tls"
CONF_TOPIC_PREFIX = "topic_prefix"
CONF_DISCOVERY_ENABLED = "discovery_enabled"
CONF_DISCOVERY_PREFIX = "discovery_prefix"
CONF_RETAIN = "retain"
CONF_QOS = "qos"
CONF_EXPOSED_INTEGRATIONS = "exposed_integrations"
CONF_EXCLUDED_DEVICES = "excluded_devices"

# Defaults
DEFAULT_BROKER_HOST = "localhost"
DEFAULT_BROKER_PORT = 1883
DEFAULT_BROKER_TLS = False
DEFAULT_TOPIC_PREFIX = ""
DEFAULT_DISCOVERY_ENABLED = False
DEFAULT_DISCOVERY_PREFIX = "homeassistant"
DEFAULT_RETAIN = True
DEFAULT_QOS = 0

# MQTT
AVAILABILITY_TOPIC_SUFFIX = "ha2mqtt/status"
PAYLOAD_ONLINE = "online"
PAYLOAD_OFFLINE = "offline"

# Reconnect
RECONNECT_MIN_DELAY = 1
RECONNECT_MAX_DELAY = 60

# Service mapping: domain -> attribute -> (service_on, service_off, service_attr_key)
# "state" attributes use turn_on/turn_off pattern
# Other attributes use specific service calls
SERVICE_MAP: dict[str, dict[str, dict]] = {
    "light": {
        "state": {"on": "light.turn_on", "off": "light.turn_off"},
        "brightness": {"service": "light.turn_on", "attr": "brightness", "type": int},
        "color_temp": {"service": "light.turn_on", "attr": "color_temp", "type": int},
        "rgb_color": {"service": "light.turn_on", "attr": "rgb_color", "type": "rgb"},
    },
    "switch": {
        "state": {"on": "switch.turn_on", "off": "switch.turn_off"},
    },
    "climate": {
        "temperature": {"service": "climate.set_temperature", "attr": "temperature", "type": float},
        "hvac_mode": {"service": "climate.set_hvac_mode", "attr": "hvac_mode", "type": str},
        "preset_mode": {"service": "climate.set_preset_mode", "attr": "preset_mode", "type": str},
    },
    "fan": {
        "state": {"on": "fan.turn_on", "off": "fan.turn_off"},
        "percentage": {"service": "fan.set_percentage", "attr": "percentage", "type": int},
    },
    "cover": {
        "state": {"on": "cover.open_cover", "off": "cover.close_cover"},
        "position": {"service": "cover.set_cover_position", "attr": "position", "type": int},
    },
    "number": {
        "state": {"service": "number.set_value", "attr": "value", "type": float},
    },
    "select": {
        "state": {"service": "select.select_option", "attr": "option", "type": str},
    },
    "button": {
        "state": {"service": "button.press", "trigger": "press"},
    },
    "lock": {
        "state": {"on": "lock.lock", "off": "lock.unlock"},
    },
    "media_player": {
        "state": {"on": "media_player.turn_on", "off": "media_player.turn_off"},
        "volume_level": {"service": "media_player.volume_set", "attr": "volume_level", "type": float},
    },
}
```

- [ ] **Step 4: Create minimal __init__.py**

```python
"""The HA2MQTT integration."""

from .const import DOMAIN


async def async_setup_entry(hass, entry):
    """Set up HA2MQTT from a config entry."""
    return True


async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    return True
```

- [ ] **Step 5: Create test scaffold**

Create `tests/__init__.py` (empty).

Create `tests/conftest.py`:

```python
"""Shared test fixtures for HA2MQTT tests."""

import pytest


@pytest.fixture
def default_config():
    """Return a default config dict for testing."""
    return {
        "broker_host": "localhost",
        "broker_port": 1883,
        "broker_username": "",
        "broker_password": "",
        "broker_tls": False,
        "topic_prefix": "",
        "discovery_enabled": False,
        "discovery_prefix": "homeassistant",
        "retain": True,
        "qos": 0,
        "exposed_integrations": [],
        "excluded_devices": [],
    }
```

Create `tests/test_const.py`:

```python
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
```

- [ ] **Step 6: Run tests**

Run: `cd /Users/radaiko/dev/private/ha2mqtt && python -m pytest tests/test_const.py -v`
Expected: 4 tests PASS

- [ ] **Step 7: Commit**

```bash
git add custom_components/ hacs.json tests/
git commit -m "feat: project scaffold with manifest, constants, and service map"
```

---

### Task 2: MQTT Bridge

**Files:**
- Create: `custom_components/ha2mqtt/mqtt_bridge.py`
- Create: `tests/test_mqtt_bridge.py`

- [ ] **Step 1: Write failing tests for MQTTBridge**

Create `tests/test_mqtt_bridge.py`:

```python
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
    result = bridge.build_set_topic("homekit", "light", "lamp", "brightness")
    assert result == "homekit/light/lamp/brightness/set"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_mqtt_bridge.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement MQTTBridge**

Create `custom_components/ha2mqtt/mqtt_bridge.py`:

```python
"""MQTT connection management for HA2MQTT."""

from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any, Callable, Coroutine

import aiomqtt

from .const import (
    AVAILABILITY_TOPIC_SUFFIX,
    PAYLOAD_OFFLINE,
    PAYLOAD_ONLINE,
    RECONNECT_MAX_DELAY,
    RECONNECT_MIN_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class MQTTBridge:
    """Manages the MQTT connection lifecycle."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.host: str = config["host"]
        self.port: int = config["port"]
        self.username: str | None = config.get("username")
        self.password: str | None = config.get("password")
        self.tls: bool = config.get("tls", False)
        self.topic_prefix: str = config.get("topic_prefix", "")
        self.retain: bool = config.get("retain", True)
        self.qos: int = config.get("qos", 0)

        self._client: aiomqtt.Client | None = None
        self._listen_task: asyncio.Task | None = None
        self._message_callback: Callable[[str, str], Coroutine] | None = None
        self.connected: bool = False
        self._shutdown: bool = False

    @property
    def availability_topic(self) -> str:
        """Return the availability topic."""
        if self.topic_prefix:
            return f"{self.topic_prefix}/{AVAILABILITY_TOPIC_SUFFIX}"
        return AVAILABILITY_TOPIC_SUFFIX

    def build_topic(self, integration: str, device_class: str, device_name: str, attribute: str) -> str:
        """Build a state topic path."""
        parts = [integration, device_class, device_name, attribute]
        if self.topic_prefix:
            parts.insert(0, self.topic_prefix)
        return "/".join(parts)

    def build_set_topic(self, integration: str, device_class: str, device_name: str, attribute: str) -> str:
        """Build a set (command) topic path."""
        return self.build_topic(integration, device_class, device_name, attribute) + "/set"

    def _build_subscribe_pattern(self) -> str:
        """Build the wildcard subscribe pattern for set topics."""
        if self.topic_prefix:
            return f"{self.topic_prefix}/+/+/+/+/set"
        return "+/+/+/+/set"

    async def connect(self) -> None:
        """Connect to the MQTT broker with LWT."""
        tls_params = ssl.create_default_context() if self.tls else None

        self._client = aiomqtt.Client(
            hostname=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            tls_params=tls_params,
            will=aiomqtt.Will(
                topic=self.availability_topic,
                payload=PAYLOAD_OFFLINE,
                qos=self.qos,
                retain=True,
            ),
        )
        await self._client.__aenter__()
        self.connected = True
        _LOGGER.info("Connected to MQTT broker at %s:%s", self.host, self.port)

        # Publish online status
        await self.publish(self.availability_topic, PAYLOAD_ONLINE, retain=True)

        # Subscribe to set topics
        pattern = self._build_subscribe_pattern()
        await self._client.subscribe(pattern, qos=self.qos)
        _LOGGER.debug("Subscribed to %s", pattern)

    async def disconnect(self) -> None:
        """Disconnect from the MQTT broker cleanly."""
        self._shutdown = True

        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass

        if self._client and self.connected:
            await self.publish(self.availability_topic, PAYLOAD_OFFLINE, retain=True)
            await self._client.__aexit__(None, None, None)
            self.connected = False
            _LOGGER.info("Disconnected from MQTT broker")

    async def publish(self, topic: str, payload: str, retain: bool | None = None) -> None:
        """Publish a message to MQTT."""
        if not self._client or not self.connected:
            _LOGGER.warning("Cannot publish to %s: not connected", topic)
            return

        use_retain = retain if retain is not None else self.retain
        await self._client.publish(topic, payload, qos=self.qos, retain=use_retain)
        _LOGGER.debug("Published %s = %s", topic, payload)

    def set_message_callback(self, callback: Callable[[str, str], Coroutine]) -> None:
        """Set the callback for incoming MQTT messages."""
        self._message_callback = callback

    async def start_listening(self) -> None:
        """Start listening for incoming MQTT messages."""
        self._listen_task = asyncio.create_task(self._listen_loop())

    async def _listen_loop(self) -> None:
        """Listen for incoming MQTT messages."""
        if not self._client:
            return
        try:
            async for message in self._client.messages:
                topic = str(message.topic)
                payload = message.payload.decode("utf-8") if isinstance(message.payload, bytes) else str(message.payload)
                _LOGGER.debug("Received %s = %s", topic, payload)
                if self._message_callback:
                    await self._message_callback(topic, payload)
        except asyncio.CancelledError:
            pass
        except aiomqtt.MqttError as err:
            if not self._shutdown:
                _LOGGER.warning("MQTT connection lost: %s", err)
                self.connected = False

    async def reconnect_loop(self) -> None:
        """Reconnect loop with exponential backoff."""
        delay = RECONNECT_MIN_DELAY
        while not self._shutdown:
            if not self.connected:
                try:
                    await self.connect()
                    await self.start_listening()
                    delay = RECONNECT_MIN_DELAY
                except (aiomqtt.MqttError, OSError) as err:
                    _LOGGER.warning(
                        "MQTT reconnect failed: %s. Retrying in %ss", err, delay
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, RECONNECT_MAX_DELAY)
            else:
                await asyncio.sleep(1)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_mqtt_bridge.py -v`
Expected: 6 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha2mqtt/mqtt_bridge.py tests/test_mqtt_bridge.py
git commit -m "feat: add MQTT bridge with connection management, topic building, and LWT"
```

---

### Task 3: Device Resolver

**Files:**
- Create: `custom_components/ha2mqtt/device_resolver.py`
- Create: `tests/test_device_resolver.py`

- [ ] **Step 1: Write failing tests for DeviceResolver**

Create `tests/test_device_resolver.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_device_resolver.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement DeviceResolver**

Create `custom_components/ha2mqtt/device_resolver.py`:

```python
"""Maps HA entities to MQTT topic parts."""

from __future__ import annotations

import re
import unicodedata


def slugify_name(name: str) -> str:
    """Convert a device name to a slug suitable for MQTT topics."""
    # Normalize unicode (e.g., ü -> u)
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    # Lowercase
    name = name.lower()
    # Replace non-alphanumeric with underscores
    name = re.sub(r"[^a-z0-9]+", "_", name)
    # Strip leading/trailing underscores
    name = name.strip("_")
    return name


class DeviceResolver:
    """Resolves HA entities to MQTT topic parts and back."""

    def __init__(self) -> None:
        self._entity_map: dict[str, dict] = {}
        # Reverse lookup: (integration, device_class, device_name) -> entity_id
        self._topic_to_entity: dict[tuple[str, str, str], str] = {}
        # Track slugified names per (integration, domain) to handle duplicates
        self._name_counts: dict[tuple[str, str, str], int] = {}

    def _get_unique_slug(self, integration: str, domain: str, raw_name: str) -> str:
        """Get a unique slugified name, adding suffix for duplicates."""
        base_slug = slugify_name(raw_name)
        key = (integration, domain, base_slug)

        if key not in self._name_counts:
            self._name_counts[key] = 1
            return base_slug

        self._name_counts[key] += 1
        return f"{base_slug}_{self._name_counts[key]}"

    def register_entity(
        self,
        entity_id: str,
        integration: str,
        device_name: str,
        domain: str,
    ) -> None:
        """Register an entity for MQTT topic resolution."""
        slug = self._get_unique_slug(integration, domain, device_name)

        entry = {
            "integration": integration,
            "device_class": domain,
            "device_name": slug,
        }
        self._entity_map[entity_id] = entry
        self._topic_to_entity[(integration, domain, slug)] = entity_id

    def unregister_entity(self, entity_id: str) -> None:
        """Remove an entity from the resolver."""
        entry = self._entity_map.pop(entity_id, None)
        if entry:
            key = (entry["integration"], entry["device_class"], entry["device_name"])
            self._topic_to_entity.pop(key, None)

    def resolve(self, entity_id: str) -> dict | None:
        """Resolve an entity_id to its MQTT topic parts."""
        return self._entity_map.get(entity_id)

    def get_entity_id(self, integration: str, device_class: str, device_name: str) -> str | None:
        """Look up an entity_id from topic parts."""
        return self._topic_to_entity.get((integration, device_class, device_name))

    def get_all_entity_ids(self) -> list[str]:
        """Return all registered entity IDs."""
        return list(self._entity_map.keys())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_device_resolver.py -v`
Expected: 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha2mqtt/device_resolver.py tests/test_device_resolver.py
git commit -m "feat: add device resolver with entity-to-topic mapping and duplicate handling"
```

---

### Task 4: Exposure Manager

**Files:**
- Create: `custom_components/ha2mqtt/exposure_manager.py`
- Create: `tests/test_exposure_manager.py`

- [ ] **Step 1: Write failing tests for ExposureManager**

Create `tests/test_exposure_manager.py`:

```python
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
    # identifiers is a set of (domain, id) tuples
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
        manager = ExposureManager(
            exposed_integrations=["hue"],
            excluded_devices=[],
        )
        devices = {"dev1": _make_device("dev1", "Lamp", "hue")}
        entities = [_make_entity("light.lamp", "light", "dev1", "hue")]
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}

        manager.rebuild(devices, entities, config_entries)

        assert manager.is_exposed("light.lamp") is True

    def test_entity_not_exposed_when_integration_not_selected(self):
        manager = ExposureManager(
            exposed_integrations=["hue"],
            excluded_devices=[],
        )
        devices = {"dev1": _make_device("dev1", "Switch", "zwave")}
        entities = [_make_entity("switch.z", "switch", "dev1", "zwave")]
        config_entries = {"entry_zwave": _make_config_entry("entry_zwave", "zwave")}

        manager.rebuild(devices, entities, config_entries)

        assert manager.is_exposed("switch.z") is False

    def test_device_excluded_overrides_integration(self):
        manager = ExposureManager(
            exposed_integrations=["hue"],
            excluded_devices=["dev1"],
        )
        devices = {"dev1": _make_device("dev1", "Lamp", "hue")}
        entities = [_make_entity("light.lamp", "light", "dev1", "hue")]
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}

        manager.rebuild(devices, entities, config_entries)

        assert manager.is_exposed("light.lamp") is False

    def test_entity_without_device_not_exposed(self):
        manager = ExposureManager(
            exposed_integrations=["hue"],
            excluded_devices=[],
        )
        entities = [_make_entity("sensor.standalone", "sensor", None, "hue")]

        manager.rebuild({}, entities, {})

        assert manager.is_exposed("sensor.standalone") is False

    def test_disabled_entity_not_exposed(self):
        manager = ExposureManager(
            exposed_integrations=["hue"],
            excluded_devices=[],
        )
        devices = {"dev1": _make_device("dev1", "Lamp", "hue")}
        entity = _make_entity("light.lamp", "light", "dev1", "hue")
        entity.disabled = True
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}

        manager.rebuild(devices, entities=[entity], config_entries=config_entries)

        assert manager.is_exposed("light.lamp") is False

    def test_get_exposed_entities(self):
        manager = ExposureManager(
            exposed_integrations=["hue"],
            excluded_devices=[],
        )
        devices = {
            "dev1": _make_device("dev1", "Lamp", "hue"),
            "dev2": _make_device("dev2", "Sensor", "hue"),
        }
        entities = [
            _make_entity("light.lamp", "light", "dev1", "hue"),
            _make_entity("sensor.temp", "sensor", "dev2", "hue"),
        ]
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}

        manager.rebuild(devices, entities, config_entries)

        exposed = manager.get_exposed_entities()
        assert len(exposed) == 2

    def test_get_entity_info(self):
        manager = ExposureManager(
            exposed_integrations=["hue"],
            excluded_devices=[],
        )
        devices = {"dev1": _make_device("dev1", "Lamp", "hue")}
        entities = [_make_entity("light.lamp", "light", "dev1", "hue")]
        config_entries = {"entry_hue": _make_config_entry("entry_hue", "hue")}

        manager.rebuild(devices, entities, config_entries)

        info = manager.get_entity_info("light.lamp")
        assert info["integration"] == "hue"
        assert info["device_name"] == "Lamp"
        assert info["domain"] == "light"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_exposure_manager.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement ExposureManager**

Create `custom_components/ha2mqtt/exposure_manager.py`:

```python
"""Manages which integrations and devices are exposed to MQTT."""

from __future__ import annotations

import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


class ExposureManager:
    """Determines which entities should be bridged to MQTT."""

    def __init__(
        self,
        exposed_integrations: list[str],
        excluded_devices: list[str],
    ) -> None:
        self._exposed_integrations = set(exposed_integrations)
        self._excluded_devices = set(excluded_devices)
        # entity_id -> info dict
        self._exposed: dict[str, dict[str, Any]] = {}
        # config_entry_id -> integration domain
        self._entry_to_integration: dict[str, str] = {}

    def rebuild(
        self,
        devices: dict[str, Any],
        entities: list[Any],
        config_entries: dict[str, Any],
    ) -> None:
        """Rebuild the exposure map from current registries."""
        self._exposed.clear()

        # Map config entry IDs to integration domains
        self._entry_to_integration = {
            entry_id: entry.domain for entry_id, entry in config_entries.items()
        }

        # Map device_id -> (integration, device_name)
        device_info: dict[str, tuple[str, str]] = {}
        for device_id, device in devices.items():
            integration = self._get_device_integration(device)
            if integration and integration in self._exposed_integrations:
                if device_id not in self._excluded_devices:
                    name = device.name_by_user or device.name or device_id
                    device_info[device_id] = (integration, name)

        # Map entities to their devices
        for entity in entities:
            if entity.disabled:
                continue
            if entity.device_id is None:
                continue
            if entity.device_id not in device_info:
                continue

            integration, device_name = device_info[entity.device_id]
            self._exposed[entity.entity_id] = {
                "integration": integration,
                "device_name": device_name,
                "domain": entity.domain,
                "device_id": entity.device_id,
            }

        _LOGGER.info("Exposure map rebuilt: %d entities exposed", len(self._exposed))

    def _get_device_integration(self, device: Any) -> str | None:
        """Get the integration domain for a device."""
        for entry_id in device.config_entries:
            if entry_id in self._entry_to_integration:
                return self._entry_to_integration[entry_id]
        return None

    def is_exposed(self, entity_id: str) -> bool:
        """Check if an entity is exposed."""
        return entity_id in self._exposed

    def get_exposed_entities(self) -> dict[str, dict[str, Any]]:
        """Return all exposed entities and their info."""
        return dict(self._exposed)

    def get_entity_info(self, entity_id: str) -> dict[str, Any] | None:
        """Get info for a specific exposed entity."""
        return self._exposed.get(entity_id)

    def update_config(
        self,
        exposed_integrations: list[str],
        excluded_devices: list[str],
    ) -> None:
        """Update exposure configuration."""
        self._exposed_integrations = set(exposed_integrations)
        self._excluded_devices = set(excluded_devices)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_exposure_manager.py -v`
Expected: 7 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha2mqtt/exposure_manager.py tests/test_exposure_manager.py
git commit -m "feat: add exposure manager for integration/device filtering"
```

---

### Task 5: State Publisher

**Files:**
- Create: `custom_components/ha2mqtt/state_publisher.py`
- Create: `tests/test_state_publisher.py`

- [ ] **Step 1: Write failing tests for StatePublisher**

Create `tests/test_state_publisher.py`:

```python
"""Tests for the state publisher."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from custom_components.ha2mqtt.state_publisher import StatePublisher


@pytest.fixture
def mock_bridge():
    bridge = MagicMock()
    bridge.build_topic = MagicMock(side_effect=lambda i, d, n, a: f"{i}/{d}/{n}/{a}")
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
    async def test_publish_attributes_as_strings(self, publisher, mock_bridge, mock_resolver, mock_exposure):
        mock_exposure.is_exposed.return_value = True
        mock_resolver.resolve.return_value = {
            "integration": "hue",
            "device_class": "sensor",
            "device_name": "temp",
        }

        state = MagicMock()
        state.state = "22.5"
        state.attributes = {"unit_of_measurement": "°C"}

        await publisher.publish_state("sensor.temp", state)

        calls = mock_bridge.publish.call_args_list
        # Should have published state and unit_of_measurement
        assert len(calls) == 2
        # All payloads should be strings
        for call in calls:
            payload = call[0][1]
            assert isinstance(payload, str)

    @pytest.mark.asyncio
    async def test_skip_internal_attributes(self, publisher, mock_bridge, mock_resolver, mock_exposure):
        mock_exposure.is_exposed.return_value = True
        mock_resolver.resolve.return_value = {
            "integration": "hue",
            "device_class": "light",
            "device_name": "lamp",
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
        assert "hue/light/lamp/brightness" in topics_published
        # Internal attributes should NOT be published
        assert "hue/light/lamp/friendly_name" not in topics_published
        assert "hue/light/lamp/supported_features" not in topics_published
        assert "hue/light/lamp/entity_picture" not in topics_published
        assert "hue/light/lamp/icon" not in topics_published
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_state_publisher.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement StatePublisher**

Create `custom_components/ha2mqtt/state_publisher.py`:

```python
"""Publishes HA entity state changes to MQTT."""

from __future__ import annotations

import json
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)

# Attributes that are internal to HA and should not be published
SKIP_ATTRIBUTES = {
    "friendly_name",
    "supported_features",
    "supported_color_modes",
    "entity_picture",
    "icon",
    "assumed_state",
    "attribution",
    "device_class",
    "state_class",
    "unit_of_measurement_precision",
}


class StatePublisher:
    """Listens for state changes and publishes to MQTT."""

    def __init__(self, bridge: Any, resolver: Any, exposure: Any) -> None:
        self._bridge = bridge
        self._resolver = resolver
        self._exposure = exposure

    async def publish_state(self, entity_id: str, state: Any) -> None:
        """Publish an entity's current state and attributes to MQTT."""
        if not self._exposure.is_exposed(entity_id):
            return

        parts = self._resolver.resolve(entity_id)
        if parts is None:
            return

        integration = parts["integration"]
        device_class = parts["device_class"]
        device_name = parts["device_name"]

        # Publish main state
        topic = self._bridge.build_topic(integration, device_class, device_name, "state")
        await self._bridge.publish(topic, str(state.state))

        # Publish each attribute
        for attr_name, attr_value in state.attributes.items():
            if attr_name in SKIP_ATTRIBUTES:
                continue

            topic = self._bridge.build_topic(integration, device_class, device_name, attr_name)
            await self._bridge.publish(topic, self._format_value(attr_value))

    async def publish_all_states(self, hass: Any) -> None:
        """Publish current state of all exposed entities (initial sync)."""
        exposed = self._exposure.get_exposed_entities()
        for entity_id in exposed:
            state = hass.states.get(entity_id)
            if state is not None:
                await self.publish_state(entity_id, state)
        _LOGGER.info("Initial state sync: published %d entities", len(exposed))

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format an attribute value as a string for MQTT."""
        if isinstance(value, (list, dict)):
            return json.dumps(value)
        return str(value)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_state_publisher.py -v`
Expected: 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha2mqtt/state_publisher.py tests/test_state_publisher.py
git commit -m "feat: add state publisher with attribute filtering and initial sync"
```

---

### Task 6: Command Handler

**Files:**
- Create: `custom_components/ha2mqtt/command_handler.py`
- Create: `tests/test_command_handler.py`

- [ ] **Step 1: Write failing tests for CommandHandler**

Create `tests/test_command_handler.py`:

```python
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
        mock_resolver.get_entity_id.return_value = "light.lamp"

        await handler.handle_message("homekit/light/lamp/brightness/set", "128")

        mock_hass.services.async_call.assert_called_once_with(
            "light", "turn_on", {"entity_id": "light.lamp", "brightness": 128}
        )

    @pytest.mark.asyncio
    async def test_climate_temperature(self, handler, mock_hass, mock_resolver):
        mock_resolver.get_entity_id.return_value = "climate.thermostat"

        await handler.handle_message("matter/climate/thermostat/temperature/set", "22.0")

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

        await handler.handle_message("hue/cover/blinds/position/set", "50")

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_command_handler.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement CommandHandler**

Create `custom_components/ha2mqtt/command_handler.py`:

```python
"""Handles inbound MQTT commands and routes them to HA services."""

from __future__ import annotations

import json
import logging
from typing import Any

from .const import SERVICE_MAP

_LOGGER = logging.getLogger(__name__)


class CommandHandler:
    """Parses MQTT set messages and calls HA services."""

    def __init__(self, hass: Any, resolver: Any, topic_prefix: str = "") -> None:
        self._hass = hass
        self._resolver = resolver
        self._topic_prefix = topic_prefix

    async def handle_message(self, topic: str, payload: str) -> None:
        """Handle an incoming MQTT set message."""
        parts = self._parse_topic(topic)
        if parts is None:
            _LOGGER.warning("Could not parse set topic: %s", topic)
            return

        integration, device_class, device_name, attribute = parts

        # Look up the entity
        entity_id = self._resolver.get_entity_id(integration, device_class, device_name)
        if entity_id is None:
            _LOGGER.warning("No entity found for %s/%s/%s", integration, device_class, device_name)
            return

        # Get the domain from the entity_id
        domain = entity_id.split(".")[0]

        # Look up the service mapping
        domain_map = SERVICE_MAP.get(domain)
        if domain_map is None:
            _LOGGER.warning("No service mapping for domain: %s", domain)
            return

        attr_map = domain_map.get(attribute)
        if attr_map is None:
            _LOGGER.warning("No service mapping for %s.%s", domain, attribute)
            return

        await self._call_service(entity_id, domain, attr_map, payload)

    def _parse_topic(self, topic: str) -> tuple[str, str, str, str] | None:
        """Parse a set topic into (integration, device_class, device_name, attribute).

        Expected format: [prefix/]integration/device_class/device_name/attribute/set
        """
        parts = topic.split("/")

        # Remove trailing "set"
        if not parts or parts[-1] != "set":
            return None
        parts = parts[:-1]

        # Remove prefix if configured
        if self._topic_prefix:
            prefix_parts = self._topic_prefix.split("/")
            if parts[: len(prefix_parts)] == prefix_parts:
                parts = parts[len(prefix_parts) :]

        if len(parts) != 4:
            return None

        return parts[0], parts[1], parts[2], parts[3]

    async def _call_service(
        self, entity_id: str, domain: str, attr_map: dict, payload: str
    ) -> None:
        """Call the appropriate HA service."""
        service_data = {"entity_id": entity_id}

        # on/off toggle pattern
        if "on" in attr_map and "off" in attr_map:
            value = payload.lower()
            if value in ("on", "open", "lock"):
                service_call = attr_map["on"]
            elif value in ("off", "close", "unlock"):
                service_call = attr_map["off"]
            else:
                _LOGGER.warning("Unknown toggle value for %s: %s", entity_id, payload)
                return

        # Trigger pattern (e.g., button press)
        elif "trigger" in attr_map:
            service_call = attr_map["service"]

        # Value-setting pattern
        elif "service" in attr_map:
            service_call = attr_map["service"]
            attr_key = attr_map["attr"]
            value_type = attr_map["type"]

            if value_type == "rgb":
                service_data[attr_key] = json.loads(payload)
            elif value_type == int:
                service_data[attr_key] = int(float(payload))
            elif value_type == float:
                service_data[attr_key] = float(payload)
            else:
                service_data[attr_key] = payload
        else:
            _LOGGER.warning("Unknown mapping format for %s", entity_id)
            return

        # Split "domain.service" into domain and service name
        svc_domain, svc_name = service_call.split(".", 1)
        await self._hass.services.async_call(svc_domain, svc_name, service_data)
        _LOGGER.debug("Called %s with %s", service_call, service_data)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/test_command_handler.py -v`
Expected: 10 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha2mqtt/command_handler.py tests/test_command_handler.py
git commit -m "feat: add command handler with domain-based MQTT-to-HA service routing"
```

---

### Task 7: Config Flow

**Files:**
- Create: `custom_components/ha2mqtt/config_flow.py`
- Create: `custom_components/ha2mqtt/strings.json`
- Create: `custom_components/ha2mqtt/translations/en.json`
- Create: `tests/test_config_flow.py`

- [ ] **Step 1: Write failing tests for ConfigFlow**

Create `tests/test_config_flow.py`:

```python
"""Tests for the config flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ha2mqtt.config_flow import Ha2MqttConfigFlow
from custom_components.ha2mqtt.const import DOMAIN


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    # Mock config entries to check for existing entries
    hass.config_entries = MagicMock()
    hass.config_entries.async_entries.return_value = []
    return hass


class TestConfigFlow:
    @pytest.mark.asyncio
    async def test_step_user_shows_broker_form(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config_entries = MagicMock()
        flow.hass.config_entries.async_entries.return_value = []

        result = await flow.async_step_user(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "user"

    @pytest.mark.asyncio
    async def test_step_user_with_valid_broker(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config_entries = MagicMock()
        flow.hass.config_entries.async_entries.return_value = []

        with patch(
            "custom_components.ha2mqtt.config_flow.test_mqtt_connection",
            new_callable=AsyncMock,
            return_value=True,
        ):
            result = await flow.async_step_user(
                user_input={
                    "broker_host": "localhost",
                    "broker_port": 1883,
                    "broker_username": "",
                    "broker_password": "",
                    "broker_tls": False,
                    "topic_prefix": "",
                }
            )

        assert result["type"] == "form"
        assert result["step_id"] == "features"

    @pytest.mark.asyncio
    async def test_step_user_with_invalid_broker(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow.hass.config_entries = MagicMock()
        flow.hass.config_entries.async_entries.return_value = []

        with patch(
            "custom_components.ha2mqtt.config_flow.test_mqtt_connection",
            new_callable=AsyncMock,
            return_value=False,
        ):
            result = await flow.async_step_user(
                user_input={
                    "broker_host": "badhost",
                    "broker_port": 1883,
                    "broker_username": "",
                    "broker_password": "",
                    "broker_tls": False,
                    "topic_prefix": "",
                }
            )

        assert result["type"] == "form"
        assert result["errors"]["base"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_step_features_advances_to_integrations(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow._broker_config = {
            "broker_host": "localhost",
            "broker_port": 1883,
        }

        result = await flow.async_step_features(
            user_input={
                "discovery_enabled": False,
                "discovery_prefix": "homeassistant",
                "retain": True,
                "qos": 0,
            }
        )

        assert result["type"] == "form"
        assert result["step_id"] == "integrations"

    @pytest.mark.asyncio
    async def test_step_integrations_creates_entry(self):
        flow = Ha2MqttConfigFlow()
        flow.hass = MagicMock()
        flow._broker_config = {
            "broker_host": "localhost",
            "broker_port": 1883,
            "broker_username": "",
            "broker_password": "",
            "broker_tls": False,
            "topic_prefix": "",
        }
        flow._features_config = {
            "discovery_enabled": False,
            "discovery_prefix": "homeassistant",
            "retain": True,
            "qos": 0,
        }

        # Mock async_create_entry
        flow.async_create_entry = MagicMock(return_value={"type": "create_entry"})

        result = await flow.async_step_integrations(
            user_input={"exposed_integrations": ["hue", "matter"]}
        )

        assert result["type"] == "create_entry"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement config_flow.py**

Create `custom_components/ha2mqtt/config_flow.py`:

```python
"""Config flow for HA2MQTT."""

from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any

import aiomqtt
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_entry_flow

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
            # Test connection
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
            # Combine all config and create entry
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

        # Get list of installed integrations
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
        """Get the options flow handler."""
        return Ha2MqttOptionsFlow(config_entry)


class Ha2MqttOptionsFlow(OptionsFlow):
    """Handle options flow for HA2MQTT."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
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
```

- [ ] **Step 4: Create strings.json**

Create `custom_components/ha2mqtt/strings.json`:

```json
{
  "config": {
    "step": {
      "user": {
        "title": "MQTT Broker",
        "description": "Configure the MQTT broker connection.",
        "data": {
          "broker_host": "Host",
          "broker_port": "Port",
          "broker_username": "Username",
          "broker_password": "Password",
          "broker_tls": "Use TLS",
          "topic_prefix": "Topic Prefix"
        }
      },
      "features": {
        "title": "Features",
        "description": "Configure optional features.",
        "data": {
          "discovery_enabled": "Enable MQTT Discovery",
          "discovery_prefix": "Discovery Prefix",
          "retain": "Retain Messages",
          "qos": "QoS Level"
        }
      },
      "integrations": {
        "title": "Integrations",
        "description": "Select which integrations to expose via MQTT.",
        "data": {
          "exposed_integrations": "Integrations"
        }
      }
    },
    "error": {
      "cannot_connect": "Cannot connect to MQTT broker. Check host, port, and credentials."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "HA2MQTT Options",
        "data": {
          "exposed_integrations": "Exposed Integrations",
          "excluded_devices": "Excluded Devices"
        }
      }
    }
  }
}
```

- [ ] **Step 5: Create translations/en.json**

Create `custom_components/ha2mqtt/translations/en.json` with identical content to `strings.json` (HA uses both — `strings.json` is the source, `translations/en.json` is the compiled version):

```json
{
  "config": {
    "step": {
      "user": {
        "title": "MQTT Broker",
        "description": "Configure the MQTT broker connection.",
        "data": {
          "broker_host": "Host",
          "broker_port": "Port",
          "broker_username": "Username",
          "broker_password": "Password",
          "broker_tls": "Use TLS",
          "topic_prefix": "Topic Prefix"
        }
      },
      "features": {
        "title": "Features",
        "description": "Configure optional features.",
        "data": {
          "discovery_enabled": "Enable MQTT Discovery",
          "discovery_prefix": "Discovery Prefix",
          "retain": "Retain Messages",
          "qos": "QoS Level"
        }
      },
      "integrations": {
        "title": "Integrations",
        "description": "Select which integrations to expose via MQTT.",
        "data": {
          "exposed_integrations": "Integrations"
        }
      }
    },
    "error": {
      "cannot_connect": "Cannot connect to MQTT broker. Check host, port, and credentials."
    }
  },
  "options": {
    "step": {
      "init": {
        "title": "HA2MQTT Options",
        "data": {
          "exposed_integrations": "Exposed Integrations",
          "excluded_devices": "Excluded Devices"
        }
      }
    }
  }
}
```

- [ ] **Step 6: Run tests**

Run: `python -m pytest tests/test_config_flow.py -v`
Expected: 5 tests PASS

- [ ] **Step 7: Commit**

```bash
git add custom_components/ha2mqtt/config_flow.py custom_components/ha2mqtt/strings.json custom_components/ha2mqtt/translations/ tests/test_config_flow.py
git commit -m "feat: add config flow with broker validation, feature toggles, and integration selection"
```

---

### Task 8: Integration Setup (__init__.py)

**Files:**
- Modify: `custom_components/ha2mqtt/__init__.py`
- Create: `tests/test_init.py`

- [ ] **Step 1: Write failing tests for setup/unload**

Create `tests/test_init.py`:

```python
"""Tests for the HA2MQTT integration setup."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.ha2mqtt import async_setup_entry, async_unload_entry
from custom_components.ha2mqtt.const import DOMAIN


@pytest.fixture
def mock_hass():
    hass = MagicMock()
    hass.data = {}
    hass.bus = MagicMock()
    hass.bus.async_listen = MagicMock(return_value=MagicMock())
    hass.states = MagicMock()
    hass.config_entries = MagicMock()
    return hass


@pytest.fixture
def mock_entry():
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {
        "broker_host": "localhost",
        "broker_port": 1883,
        "broker_username": "",
        "broker_password": "",
        "broker_tls": False,
        "topic_prefix": "",
        "discovery_enabled": False,
        "discovery_prefix": "homeassistant",
        "retain": True,
        "qos": 0,
    }
    entry.options = {
        "exposed_integrations": ["hue"],
        "excluded_devices": [],
    }
    entry.add_update_listener = MagicMock()
    return entry


class TestSetup:
    @pytest.mark.asyncio
    async def test_setup_entry_stores_runtime_data(self, mock_hass, mock_entry):
        with patch(
            "custom_components.ha2mqtt.MQTTBridge"
        ) as mock_bridge_cls:
            mock_bridge = AsyncMock()
            mock_bridge.connected = True
            mock_bridge_cls.return_value = mock_bridge

            with patch("custom_components.ha2mqtt.DeviceResolver"):
                with patch("custom_components.ha2mqtt.ExposureManager"):
                    with patch("custom_components.ha2mqtt.StatePublisher"):
                        with patch("custom_components.ha2mqtt.CommandHandler"):
                            result = await async_setup_entry(mock_hass, mock_entry)

        assert result is True
        assert DOMAIN in mock_hass.data
        assert mock_entry.entry_id in mock_hass.data[DOMAIN]

    @pytest.mark.asyncio
    async def test_unload_entry_disconnects(self, mock_hass, mock_entry):
        mock_bridge = AsyncMock()
        mock_hass.data = {
            DOMAIN: {
                mock_entry.entry_id: {
                    "bridge": mock_bridge,
                    "unsub_state": MagicMock(),
                    "unsub_device": MagicMock(),
                    "unsub_entity": MagicMock(),
                }
            }
        }

        result = await async_unload_entry(mock_hass, mock_entry)

        assert result is True
        mock_bridge.disconnect.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_init.py -v`
Expected: FAIL

- [ ] **Step 3: Implement full __init__.py**

Replace `custom_components/ha2mqtt/__init__.py` with:

```python
"""The HA2MQTT integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .command_handler import CommandHandler
from .const import (
    CONF_BROKER_HOST,
    CONF_BROKER_PASSWORD,
    CONF_BROKER_PORT,
    CONF_BROKER_TLS,
    CONF_BROKER_USERNAME,
    CONF_DISCOVERY_ENABLED,
    CONF_EXCLUDED_DEVICES,
    CONF_EXPOSED_INTEGRATIONS,
    CONF_QOS,
    CONF_RETAIN,
    CONF_TOPIC_PREFIX,
    DOMAIN,
)
from .device_resolver import DeviceResolver
from .exposure_manager import ExposureManager
from .mqtt_bridge import MQTTBridge
from .state_publisher import StatePublisher

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA2MQTT from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Build MQTT bridge config
    bridge_config = {
        "host": entry.data[CONF_BROKER_HOST],
        "port": entry.data[CONF_BROKER_PORT],
        "username": entry.data.get(CONF_BROKER_USERNAME) or None,
        "password": entry.data.get(CONF_BROKER_PASSWORD) or None,
        "tls": entry.data.get(CONF_BROKER_TLS, False),
        "topic_prefix": entry.data.get(CONF_TOPIC_PREFIX, ""),
        "retain": entry.data.get(CONF_RETAIN, True),
        "qos": entry.data.get(CONF_QOS, 0),
    }

    # Create components
    bridge = MQTTBridge(bridge_config)
    resolver = DeviceResolver()
    exposure = ExposureManager(
        exposed_integrations=entry.options.get(CONF_EXPOSED_INTEGRATIONS, []),
        excluded_devices=entry.options.get(CONF_EXCLUDED_DEVICES, []),
    )
    publisher = StatePublisher(bridge, resolver, exposure)
    handler = CommandHandler(hass, resolver, topic_prefix=bridge_config["topic_prefix"])

    # Set message callback
    bridge.set_message_callback(handler.handle_message)

    # Build exposure map from registries
    _rebuild_maps(hass, exposure, resolver)

    # Connect to MQTT
    await bridge.connect()
    await bridge.start_listening()

    # Publish initial state
    await publisher.publish_all_states(hass)

    # Listen for state changes
    async def _on_state_changed(event: Event) -> None:
        entity_id = event.data.get("entity_id")
        new_state = event.data.get("new_state")
        if entity_id and new_state:
            await publisher.publish_state(entity_id, new_state)

    unsub_state = hass.bus.async_listen(EVENT_STATE_CHANGED, _on_state_changed)

    # Listen for registry changes
    def _on_registry_changed(event: Event) -> None:
        _rebuild_maps(hass, exposure, resolver)

    unsub_device = hass.bus.async_listen("device_registry_updated", _on_registry_changed)
    unsub_entity = hass.bus.async_listen("entity_registry_updated", _on_registry_changed)

    # Listen for options updates
    entry.add_update_listener(_on_options_updated)

    # Store runtime data
    hass.data[DOMAIN][entry.entry_id] = {
        "bridge": bridge,
        "resolver": resolver,
        "exposure": exposure,
        "publisher": publisher,
        "handler": handler,
        "unsub_state": unsub_state,
        "unsub_device": unsub_device,
        "unsub_entity": unsub_entity,
    }

    _LOGGER.info("HA2MQTT integration loaded")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if data:
        data["unsub_state"]()
        data["unsub_device"]()
        data["unsub_entity"]()
        await data["bridge"].disconnect()

    _LOGGER.info("HA2MQTT integration unloaded")
    return True


async def _on_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    data = hass.data[DOMAIN].get(entry.entry_id)
    if not data:
        return

    data["exposure"].update_config(
        exposed_integrations=entry.options.get(CONF_EXPOSED_INTEGRATIONS, []),
        excluded_devices=entry.options.get(CONF_EXCLUDED_DEVICES, []),
    )
    _rebuild_maps(hass, data["exposure"], data["resolver"])
    await data["publisher"].publish_all_states(hass)


def _rebuild_maps(hass: HomeAssistant, exposure: ExposureManager, resolver: DeviceResolver) -> None:
    """Rebuild exposure and resolver maps from current registries."""
    device_reg = dr.async_get(hass)
    entity_reg = er.async_get(hass)

    devices = {dev.id: dev for dev in device_reg.devices.values()}
    entities = list(entity_reg.entities.values())
    config_entries = {
        entry.entry_id: entry for entry in hass.config_entries.async_entries()
    }

    exposure.rebuild(devices, entities, config_entries)

    # Rebuild resolver from exposed entities
    resolver._entity_map.clear()
    resolver._topic_to_entity.clear()
    resolver._name_counts.clear()

    for entity_id, info in exposure.get_exposed_entities().items():
        resolver.register_entity(
            entity_id=entity_id,
            integration=info["integration"],
            device_name=info["device_name"],
            domain=info["domain"],
        )
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_init.py -v`
Expected: 2 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha2mqtt/__init__.py tests/test_init.py
git commit -m "feat: wire up integration setup with event listeners and registry sync"
```

---

### Task 9: Discovery Publisher (Optional Feature)

**Files:**
- Create: `custom_components/ha2mqtt/discovery.py`
- Create: `tests/test_discovery.py`

- [ ] **Step 1: Write failing tests for DiscoveryPublisher**

Create `tests/test_discovery.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_discovery.py -v`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement DiscoveryPublisher**

Create `custom_components/ha2mqtt/discovery.py`:

```python
"""Optional MQTT discovery publisher for HA2MQTT."""

from __future__ import annotations

import json
import logging
from typing import Any

from .const import SERVICE_MAP

_LOGGER = logging.getLogger(__name__)

# Domains that support command topics
SETTABLE_DOMAINS = set(SERVICE_MAP.keys())


class DiscoveryPublisher:
    """Publishes MQTT discovery config messages."""

    def __init__(self, bridge: Any, discovery_prefix: str = "homeassistant") -> None:
        self._bridge = bridge
        self._prefix = discovery_prefix

    def _discovery_topic(self, domain: str, entity_id: str) -> str:
        """Build the discovery config topic."""
        unique_id = f"ha2mqtt_{entity_id.replace('.', '_')}"
        return f"{self._prefix}/{domain}/{unique_id}/config"

    async def publish_discovery(
        self,
        entity_id: str,
        integration: str,
        device_class: str,
        device_name: str,
        attributes: list[str],
    ) -> None:
        """Publish a discovery config for an entity."""
        topic = self._discovery_topic(device_class, entity_id)

        state_topic = self._bridge.build_topic(integration, device_class, device_name, "state")

        config: dict[str, Any] = {
            "name": device_name,
            "unique_id": f"ha2mqtt_{entity_id.replace('.', '_')}",
            "state_topic": state_topic,
            "availability_topic": self._bridge.availability_topic,
            "payload_available": "online",
            "payload_not_available": "offline",
        }

        # Add command topic for settable domains
        if device_class in SETTABLE_DOMAINS:
            config["command_topic"] = state_topic + "/set"

        # Add brightness topic for lights
        if device_class == "light" and "brightness" in attributes:
            brightness_topic = self._bridge.build_topic(
                integration, device_class, device_name, "brightness"
            )
            config["brightness_state_topic"] = brightness_topic
            config["brightness_command_topic"] = brightness_topic + "/set"

        # Add color_temp topic for lights
        if device_class == "light" and "color_temp" in attributes:
            color_temp_topic = self._bridge.build_topic(
                integration, device_class, device_name, "color_temp"
            )
            config["color_temp_state_topic"] = color_temp_topic
            config["color_temp_command_topic"] = color_temp_topic + "/set"

        payload = json.dumps(config)
        await self._bridge.publish(topic, payload, retain=True)
        _LOGGER.debug("Published discovery for %s", entity_id)

    async def remove_discovery(self, domain: str, entity_id: str) -> None:
        """Remove a discovery config by publishing empty payload."""
        topic = self._discovery_topic(domain, entity_id)
        await self._bridge.publish(topic, "", retain=True)
        _LOGGER.debug("Removed discovery for %s", entity_id)

    async def publish_all(self, exposed_entities: dict[str, dict], hass: Any) -> None:
        """Publish discovery configs for all exposed entities."""
        for entity_id, info in exposed_entities.items():
            state = hass.states.get(entity_id)
            attributes = list(state.attributes.keys()) if state else []
            await self.publish_discovery(
                entity_id=entity_id,
                integration=info["integration"],
                device_class=info["domain"],
                device_name=info.get("device_name_slug", entity_id),
                attributes=attributes,
            )

    async def remove_all(self, exposed_entities: dict[str, dict]) -> None:
        """Remove discovery configs for all exposed entities."""
        for entity_id, info in exposed_entities.items():
            await self.remove_discovery(info["domain"], entity_id)
```

- [ ] **Step 4: Run tests**

Run: `python -m pytest tests/test_discovery.py -v`
Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add custom_components/ha2mqtt/discovery.py tests/test_discovery.py
git commit -m "feat: add optional MQTT discovery publisher"
```

---

### Task 10: Wire Discovery Into Init & Run Full Test Suite

**Files:**
- Modify: `custom_components/ha2mqtt/__init__.py`

- [ ] **Step 1: Add discovery to __init__.py setup**

Add the discovery import at the top of `__init__.py`:

```python
from .discovery import DiscoveryPublisher
```

In `async_setup_entry`, after creating the publisher and handler, add:

```python
    # Create discovery publisher if enabled
    discovery = None
    if entry.data.get(CONF_DISCOVERY_ENABLED, False):
        discovery = DiscoveryPublisher(
            bridge,
            discovery_prefix=entry.data.get("discovery_prefix", "homeassistant"),
        )
```

After `await publisher.publish_all_states(hass)`, add:

```python
    # Publish discovery if enabled
    if discovery:
        await discovery.publish_all(exposure.get_exposed_entities(), hass)
```

Add `"discovery": discovery` to the `hass.data[DOMAIN][entry.entry_id]` dict.

In `async_unload_entry`, before `await data["bridge"].disconnect()`, add:

```python
        if data.get("discovery"):
            await data["discovery"].remove_all(
                data["exposure"].get_exposed_entities()
            )
```

- [ ] **Step 2: Run the full test suite**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add custom_components/ha2mqtt/__init__.py
git commit -m "feat: wire discovery publisher into integration lifecycle"
```

---

### Task 11: Setup Tooling & Final Integration Test

**Files:**
- Create: `setup.cfg` or `pyproject.toml`
- Create: `requirements_test.txt`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "ha2mqtt"
version = "0.1.0"
requires-python = ">=3.12"

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.ruff]
target-version = "py312"
line-length = 120
```

- [ ] **Step 2: Create requirements_test.txt**

```
pytest>=8.0.0
pytest-asyncio>=0.23.0
aiomqtt>=2.0.0
homeassistant
```

- [ ] **Step 3: Install test dependencies and run full suite**

Run: `pip install -r requirements_test.txt && python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml requirements_test.txt
git commit -m "chore: add test tooling configuration"
```

- [ ] **Step 5: Push to GitHub**

```bash
git push origin main
```
