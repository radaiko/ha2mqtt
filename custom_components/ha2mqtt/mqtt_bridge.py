"""MQTT connection management for HA2MQTT."""

from __future__ import annotations

import asyncio
import logging
import ssl
from typing import Any, Callable, Coroutine

try:
    import aiomqtt
except ImportError:  # pragma: no cover
    aiomqtt = None  # type: ignore[assignment]

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

    def build_topic(self, *segments: str) -> str:
        """Build a topic path from variable segments."""
        parts = list(segments)
        if self.topic_prefix:
            parts.insert(0, self.topic_prefix)
        return "/".join(parts)

    def build_set_topic(self, *segments: str) -> str:
        """Build a set (command) topic path."""
        return self.build_topic(*segments) + "/set"

    def _build_subscribe_patterns(self) -> list[str]:
        """Build wildcard subscribe patterns for set topics.

        Two patterns:
          prefix/integration/domain/device/entity_key/set          (state set)
          prefix/integration/domain/device/entity_key/attr/set     (attribute set)
        """
        if self.topic_prefix:
            return [
                f"{self.topic_prefix}/+/+/+/+/set",
                f"{self.topic_prefix}/+/+/+/+/+/set",
            ]
        return ["+/+/+/+/set", "+/+/+/+/+/set"]

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
        for pattern in self._build_subscribe_patterns():
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
