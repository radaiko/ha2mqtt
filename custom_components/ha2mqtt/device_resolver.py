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
        # Reverse lookup: (integration, domain, device_name, entity_key) -> entity_id
        self._topic_to_entity: dict[tuple[str, str, str, str], str] = {}
        # device_id -> slug (ensures same physical device always gets same slug)
        self._device_slugs: dict[str, str] = {}
        # Track base slugs per integration to handle different devices with the same name
        self._slug_counts: dict[tuple[str, str], int] = {}

    def _get_device_slug(self, integration: str, device_name: str, device_id: str) -> str:
        """Get or create a slug for a device, reusing for same device_id."""
        # If we've already assigned a slug to this device, reuse it
        if device_id in self._device_slugs:
            return self._device_slugs[device_id]

        base_slug = slugify_name(device_name)
        key = (integration, base_slug)

        if key not in self._slug_counts:
            self._slug_counts[key] = 1
            slug = base_slug
        else:
            self._slug_counts[key] += 1
            slug = f"{base_slug}_{self._slug_counts[key]}"

        self._device_slugs[device_id] = slug
        return slug

    def register_entity(
        self,
        entity_id: str,
        integration: str,
        device_name: str,
        domain: str,
        device_id: str,
        entity_key: str,
    ) -> None:
        """Register an entity for MQTT topic resolution."""
        slug = self._get_device_slug(integration, device_name, device_id)

        entry = {
            "integration": integration,
            "device_class": domain,
            "device_name": slug,
            "entity_key": entity_key,
        }
        self._entity_map[entity_id] = entry
        self._topic_to_entity[(integration, domain, slug, entity_key)] = entity_id

    def unregister_entity(self, entity_id: str) -> None:
        """Remove an entity from the resolver."""
        entry = self._entity_map.pop(entity_id, None)
        if entry:
            key = (entry["integration"], entry["device_class"], entry["device_name"], entry["entity_key"])
            self._topic_to_entity.pop(key, None)

    def resolve(self, entity_id: str) -> dict | None:
        """Resolve an entity_id to its MQTT topic parts."""
        return self._entity_map.get(entity_id)

    def get_entity_id(self, integration: str, device_class: str, device_name: str, entity_key: str) -> str | None:
        """Look up an entity_id from topic parts."""
        return self._topic_to_entity.get((integration, device_class, device_name, entity_key))

    def get_all_entity_ids(self) -> list[str]:
        """Return all registered entity IDs."""
        return list(self._entity_map.keys())
