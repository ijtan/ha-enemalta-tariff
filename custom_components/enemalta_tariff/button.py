"""Reset button for the Enemalta Tariff Cost integration."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from .const import (
    CONF_BASELINE,
    CONF_PERIOD_START,
    CONF_SOURCE,
    CONF_SOURCE_IS_WH,
    DOMAIN,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the reset button from a config entry."""
    async_add_entities([EnemaltaResetButton(entry)])


class EnemaltaResetButton(ButtonEntity):
    """Re-baseline consumption and set the billing-period start to today."""

    _attr_has_entity_name = True
    _attr_name = "Reset billing period"
    _attr_icon = "mdi:calendar-refresh"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_reset"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
        )

    async def async_press(self) -> None:
        """Capture the current meter reading and reset the period start."""
        entry = self._entry
        state = self.hass.states.get(entry.data[CONF_SOURCE])
        baseline = entry.data.get(CONF_BASELINE, 0.0)
        if state is not None and state.state not in (
            "unknown",
            "unavailable",
            "none",
            "",
        ):
            try:
                baseline = float(state.state)
            except (TypeError, ValueError):
                pass
        # Baseline is always stored in the source sensor's raw units; the sensor
        # applies the Wh→kWh conversion afterwards.
        _ = entry.data.get(CONF_SOURCE_IS_WH)
        new_data = {
            **entry.data,
            CONF_BASELINE: baseline,
            CONF_PERIOD_START: dt_util.now().date().isoformat(),
        }
        self.hass.config_entries.async_update_entry(entry, data=new_data)
