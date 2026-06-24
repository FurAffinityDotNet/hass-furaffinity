"""Services for the Fur Affinity Status integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

REFRESH_SCHEMA = vol.Schema({})


def async_register_services(hass: HomeAssistant) -> None:
    """Register services for the integration."""

    async def _async_refresh(call: ServiceCall) -> None:
        """Force a refresh of all Fur Affinity Status coordinators."""
        for entry_id, coordinator in hass.data.get(DOMAIN, {}).items():
            _LOGGER.debug("Forcing refresh of coordinator for %s", entry_id)
            await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, "refresh", _async_refresh, schema=REFRESH_SCHEMA
    )
