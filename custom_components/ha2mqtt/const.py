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
