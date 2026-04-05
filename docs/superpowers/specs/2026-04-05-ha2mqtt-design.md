# HA2MQTT Design Spec

A HACS custom integration that bridges Home Assistant entities to MQTT bidirectionally, organized by source integration.

## Problem

Users want a generic way to expose HA device entities to MQTT — similar to what zigbee2mqtt or gv2mqtt do for specific integrations, but for **all** integration types. Currently this requires manually creating HA automations per entity, which doesn't scale.

## Architecture

### Core Components

1. **DeviceResolver** — Queries HA's device and entity registries to map each entity to its source integration and device. Builds the MQTT topic path.

2. **MQTTBridge** — Manages an independent MQTT connection via `aiomqtt`. Handles publish, subscribe, reconnect with exponential backoff, and LWT (Last Will & Testament) for availability.

3. **StatePublisher** — Listens to `state_changed` events on HA's event bus. Filters for exposed entities, resolves topic path via DeviceResolver, publishes each attribute to its subtopic.

4. **CommandHandler** — Subscribes to `<prefix>/+/+/+/+/set` wildcard topics (or `+/+/+/+/set` when no prefix is configured). Parses inbound MQTT messages and calls the appropriate HA service to apply the change.

5. **ExposureManager** — Manages which integrations and devices are exposed. Persists selections in `config_entry.options`. Listens to device/entity registry update events to dynamically rebuild the exposure map.

6. **DiscoveryPublisher** (optional) — When enabled, publishes HA MQTT discovery config messages so other systems can auto-discover entities.

### Data Flow

```
HA state change -> event bus -> StatePublisher -> MQTTBridge -> MQTT broker
MQTT broker -> CommandHandler -> hass.services.async_call -> HA entity
```

## MQTT Topic Structure

### Pattern

```
<prefix>/<integration>/<device_class>/<device_name>/<attribute>
```

- `<prefix>` — User-configurable, defaults to empty (no prefix)
- `<integration>` — Source integration identifier (e.g., `homekit_controller`, `matter`, `hue`)
- `<device_class>` — HA entity domain (e.g., `light`, `sensor`, `climate`, `switch`)
- `<device_name>` — Slugified device name from the device registry
- `<attribute>` — Individual state attribute

### State Topics (published by ha2mqtt)

```
homekit_controller/light/living_room_lamp/state        -> "on" / "off"
homekit_controller/light/living_room_lamp/brightness    -> "255"
homekit_controller/light/living_room_lamp/color_temp    -> "400"
homekit_controller/sensor/outdoor_temp/state            -> "22.5"
homekit_controller/sensor/outdoor_temp/unit             -> "C"
matter/climate/bedroom_thermostat/state                 -> "heat"
matter/climate/bedroom_thermostat/temperature           -> "21.0"
matter/climate/bedroom_thermostat/current_temperature   -> "19.5"
```

### Command Topics (subscribed by ha2mqtt)

Same path with `/set` appended:

```
homekit_controller/light/living_room_lamp/state/set         <- "on"
homekit_controller/light/living_room_lamp/brightness/set    <- "128"
matter/climate/bedroom_thermostat/temperature/set           <- "22.0"
```

### Availability Topic

```
<prefix>/ha2mqtt/status -> "online" / "offline" (via LWT)
```

### Naming Rules

- Device names are slugified (lowercase, spaces to underscores, special chars stripped)
- Duplicate device names within the same integration/class get a numeric suffix (`_2`, `_3`)
- All values published as strings

## Entity-to-Service Mapping

When a message arrives on a `/set` topic, CommandHandler calls the appropriate HA service based on the entity domain and attribute.

| Domain | Attribute | Service Call | Payload |
|--------|-----------|-------------|---------|
| `light` | `state` | `light.turn_on` / `light.turn_off` | "on"/"off" |
| `light` | `brightness` | `light.turn_on` | `{"brightness": int}` |
| `light` | `color_temp` | `light.turn_on` | `{"color_temp": int}` |
| `light` | `rgb_color` | `light.turn_on` | `{"rgb_color": [r,g,b]}` |
| `switch` | `state` | `switch.turn_on` / `switch.turn_off` | "on"/"off" |
| `climate` | `temperature` | `climate.set_temperature` | `{"temperature": float}` |
| `climate` | `hvac_mode` | `climate.set_hvac_mode` | `{"hvac_mode": str}` |
| `climate` | `preset_mode` | `climate.set_preset_mode` | `{"preset_mode": str}` |
| `fan` | `state` | `fan.turn_on` / `fan.turn_off` | "on"/"off" |
| `fan` | `percentage` | `fan.set_percentage` | `{"percentage": int}` |
| `cover` | `state` | `cover.open_cover` / `cover.close_cover` | "open"/"close" |
| `cover` | `position` | `cover.set_cover_position` | `{"position": int}` |
| `number` | `state` | `number.set_value` | `{"value": float}` |
| `select` | `state` | `select.select_option` | `{"option": str}` |
| `button` | `state` | `button.press` | "press" |
| `lock` | `state` | `lock.lock` / `lock.unlock` | "lock"/"unlock" |
| `media_player` | `state` | `media_player.turn_on` / `media_player.turn_off` | "on"/"off" |
| `media_player` | `volume_level` | `media_player.volume_set` | `{"volume_level": float}` |

Read-only entities (sensors, binary_sensors) have no `/set` topics.

The mapping is defined as a registry dict — adding new domains requires only adding an entry.

## Configuration

### Config Flow (HA UI)

**Step 1 — MQTT Broker:**
- Host (default: `localhost`)
- Port (default: `1883`)
- Username (optional)
- Password (optional)
- TLS toggle (default: off)
- Topic prefix (default: empty)

**Step 2 — Feature Toggles:**
- Enable MQTT discovery (default: off)
- Discovery prefix (default: `homeassistant`)
- Publish retain flag (default: on)
- QoS level (default: 0, options: 0/1/2)

**Step 3 — Integration Selection:**
- Multi-select list of all installed integrations
- User picks which integrations to expose

### Options Flow (reconfigurable)

- All settings from above can be changed after setup
- Per-device toggle: device list under each selected integration where individual devices can be excluded
- Adding/removing integrations without reinstalling

### Validation

- Config flow tests MQTT broker connectivity before completing setup
- Invalid broker connection shows error in UI and blocks setup

### Persistence

- All selections stored in `config_entry.options`
- UI only, no YAML config

## Startup & Shutdown

### Startup Sequence

1. Load config entry
2. Connect to MQTT broker (retry with exponential backoff if unavailable)
3. Query device/entity registries to build the exposure map
4. Publish current state of all exposed entities (initial sync)
5. Subscribe to `/set` wildcard topics for all exposed entities
6. If discovery enabled, publish discovery config messages
7. Publish availability `online` to LWT topic
8. Register `state_changed` event listener

### Shutdown

1. Unregister event listener
2. Publish availability `offline`
3. If discovery enabled, publish empty discovery configs (remove entities)
4. Disconnect MQTT cleanly

### MQTT Broker Disconnect

- Automatic reconnect with exponential backoff (1s, 2s, 4s, ... max 60s)
- State changes during disconnect are dropped (not buffered)
- On reconnect: full state republish to sync
- LWT handles availability automatically

### Dynamic Registry Changes

- Listen to `device_registry_updated` and `entity_registry_updated` events
- Rebuild exposure map dynamically — no restart needed
- New entities in exposed integrations get picked up automatically
- Removed entities get their topics cleaned up (empty retained message published)

## Logging

- Standard HA logger (`logging.getLogger(__name__)`)
- Debug: every publish/receive
- Info: connect/disconnect/reconnect, exposure map changes
- Warning: broker unreachable, unknown set command received

## Project Structure

```
ha2mqtt/
  hacs.json
  custom_components/
    ha2mqtt/
      __init__.py          # Integration setup, startup/shutdown
      manifest.json        # HA integration manifest
      config_flow.py       # Config flow + options flow
      const.py             # Constants, defaults, domain
      mqtt_bridge.py       # MQTT connection management
      state_publisher.py   # Event listener -> MQTT publish
      command_handler.py   # MQTT subscribe -> HA service calls
      device_resolver.py   # Entity/device registry mapping
      exposure_manager.py  # Integration/device selection logic
      discovery.py         # Optional MQTT discovery publisher
      strings.json         # UI strings for config flow
      translations/
        en.json            # English translations
```

### manifest.json

- `domain`: `ha2mqtt`
- `name`: `HA2MQTT`
- `dependencies`: `[]`
- `requirements`: `["aiomqtt>=2.0.0"]`
- `config_flow`: `true`
- `iot_class`: `local_push`
- `version`: `0.1.0`

### hacs.json

- `name`: `HA2MQTT`
- `render_readme`: `true`
- `homeassistant`: `"2024.1.0"` (minimum version for modern registry APIs)

### HACS Installation

Users add the repo as a custom repository in HACS, install, restart HA, then configure via the HA UI.
