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
