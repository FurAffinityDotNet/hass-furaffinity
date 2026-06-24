"""Binary sensor platform for the Fur Affinity Status integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN


@dataclass(frozen=True, kw_only=True)
class FABinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes a Fur Affinity Status binary sensor."""


BINARY_SENSOR_DESCRIPTIONS: tuple[FABinarySensorEntityDescription, ...] = (
    FABinarySensorEntityDescription(
        key="has_alerts",
        translation_key="has_alerts",
        name="Has alerts",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert",
    ),
    FABinarySensorEntityDescription(
        key="has_incidents",
        translation_key="has_incidents",
        name="Has incidents",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:flash-alert",
    ),
    FABinarySensorEntityDescription(
        key="has_maintenance",
        translation_key="has_maintenance",
        name="Has maintenance",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:wrench",
    ),
    FABinarySensorEntityDescription(
        key="is_up",
        translation_key="is_up",
        name="Operational",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:check-circle",
    )
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fur Affinity Status binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        FurAffinityStatusBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class FurAffinityStatusBinarySensor(
    CoordinatorEntity, BinarySensorEntity
):
    """Representation of a Fur Affinity Status binary sensor."""

    entity_description: FABinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator,
        description: FABinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{description.key}"
        )
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=DEFAULT_NAME,
            manufacturer="Fur Affinity",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return None

        if self.entity_description.key == "has_alerts":
            return len(self.coordinator.data.get("active_alerts") or []) > 0

        if self.entity_description.key == "has_incidents":
            return len(self.coordinator.data.get("active_incidents") or []) > 0

        if self.entity_description.key == "has_maintenance":
            return len(self.coordinator.data.get("active_maintenance") or []) > 0

        if self.entity_description.key == "is_up":
            return self.coordinator.data.get("overall_status") == "up"

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes for relevant sensors."""
        if self.coordinator.data is None:
            return None

        if self.entity_description.key == "has_alerts":
            return {
                "alerts": self.coordinator.data.get("active_alerts", []),
            }
        if self.entity_description.key == "has_incidents":
            return {
                "incidents": self.coordinator.data.get("active_incidents", []),
            }
        if self.entity_description.key == "has_maintenance":
            return {
                "maintenance": self.coordinator.data.get("active_maintenance", []),
            }
        return None
