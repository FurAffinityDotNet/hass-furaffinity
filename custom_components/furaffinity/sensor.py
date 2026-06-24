"""Sensor platform for the Fur Affinity Status integration."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN


@dataclass(frozen=True, kw_only=True)
class FASensorEntityDescription(SensorEntityDescription):
    """Describes a Fur Affinity Status sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any]
    attrs_fn: Callable[[dict[str, Any]], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[FASensorEntityDescription, ...] = (
    FASensorEntityDescription(
        key="overall_status",
        translation_key="overall_status",
        name="Overall status",
        icon="mdi:check-circle",
        device_class=SensorDeviceClass.ENUM,
        options=["operational", "down", "paused", "investigating"],
        value_fn=lambda data: data.get("overall_status"),
    ),
    FASensorEntityDescription(
        key="active_alerts",
        translation_key="active_alerts",
        name="Active alerts",
        icon="mdi:alert",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("active_alerts", [])),
        attrs_fn=lambda data: {
            "alerts": data.get("active_alerts", []),
        },
    ),
    FASensorEntityDescription(
        key="active_incidents",
        translation_key="active_incidents",
        name="Active incidents",
        icon="mdi:flash-alert",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("active_incidents", [])),
        attrs_fn=lambda data: {
            "incidents": data.get("active_incidents", []),
        },
    ),
    FASensorEntityDescription(
        key="active_maintenance",
        translation_key="active_maintenance",
        name="Active maintenance",
        icon="mdi:wrench",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: len(data.get("active_maintenance", [])),
        attrs_fn=lambda data: {
            "maintenance": data.get("active_maintenance", []),
        },
    ),
    FASensorEntityDescription(
        key="uptime_24h",
        translation_key="uptime_24h",
        name="Overall uptime 24h",
        icon="mdi:chart-line",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _avg_uptime(data.get("monitors", []), "uptime_24h"),
    ),
    FASensorEntityDescription(
        key="uptime_72h",
        translation_key="uptime_72h",
        name="Overall uptime 72h",
        icon="mdi:chart-line",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _avg_uptime(data.get("monitors", []), "uptime_72h"),
    ),
    FASensorEntityDescription(
        key="uptime_7d",
        translation_key="uptime_7d",
        name="Overall uptime 7d",
        icon="mdi:chart-line",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: _avg_uptime(data.get("monitors", []), "uptime_7d"),
    ),
)


def _avg_uptime(monitors: list[dict[str, Any]], key: str) -> float | None:
    """Return the average uptime across all monitors."""
    values: list[float] = []
    for monitor in monitors:
        v = monitor.get(key)
        if v is not None:
            values.append(float(v))
    if not values:
        return None
    return round(sum(values) / len(values), 2)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fur Affinity Status sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = [
        FurAffinityStatusSensor(coordinator, description)
        for description in SENSOR_DESCRIPTIONS
    ]

    for monitor in coordinator.data.get("monitors", []):
        entities.append(FurAffinityMonitorSensor(coordinator, monitor))

    async_add_entities(entities)


class FurAffinityStatusSensor(
    CoordinatorEntity, SensorEntity
):
    """Representation of a Fur Affinity Status sensor."""

    entity_description: FASensorEntityDescription
    _attr_has_entity_name = True

    def __init__(self, coordinator, description: FASensorEntityDescription) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=DEFAULT_NAME,
            manufacturer="Fur Affinity",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.coordinator.data is None or self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)


class FurAffinityMonitorSensor(
    CoordinatorEntity, SensorEntity
):
    """Representation of an individual monitor sensor."""

    _attr_has_entity_name = True
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["up", "down", "paused", "pending"]
    _attr_icon = "mdi:server"

    def __init__(self, coordinator, monitor: dict[str, Any]) -> None:
        """Initialize the monitor sensor."""
        super().__init__(coordinator)
        self._monitor_id = monitor["id"]
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_monitor_{monitor['id']}"
        )
        self._attr_name = monitor.get("name", f"Monitor {monitor['id']}")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.config_entry.entry_id}_{monitor['id']}")},
            name=monitor.get("name", f"Monitor {monitor['id']}"),
            manufacturer="Fur Affinity",
            model=monitor.get("monitor_type"),
            via_device=(DOMAIN, coordinator.config_entry.entry_id),
        )

    @property
    def _monitor(self) -> dict[str, Any] | None:
        if self.coordinator.data is None:
            return None
        for monitor in self.coordinator.data.get("monitors", []):
            if monitor.get("id") == self._monitor_id:
                return monitor
        return None

    @property
    def native_value(self) -> str | None:
        """Return the current status of the monitor."""
        monitor = self._monitor
        if monitor is None:
            return None
        return monitor.get("status")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return the extra state attributes for the monitor."""
        monitor = self._monitor
        if monitor is None:
            return None
        return {
            "description": monitor.get("description"),
            "monitor_type": monitor.get("monitor_type"),
            "check_interval": monitor.get("check_interval"),
            "last_checked": monitor.get("last_checked"),
            "uptime_24h": monitor.get("uptime_24h"),
            "uptime_72h": monitor.get("uptime_72h"),
            "uptime_7d": monitor.get("uptime_7d"),
            "group": (monitor.get("group") or {}).get("name"),
        }
