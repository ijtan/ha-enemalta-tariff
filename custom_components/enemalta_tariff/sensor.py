"""Cost sensor for the Enemalta Tariff Cost integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
)
import homeassistant.util.dt as dt_util

from .calc import band1_allowance, calculate_cost
from .const import (
    CONF_BASELINE,
    CONF_INCLUDE_SERVICE_CHARGE,
    CONF_PERIOD_START,
    CONF_PHASE,
    CONF_PRIMARY,
    CONF_RESIDENTS,
    CONF_SOURCE,
    CONF_SOURCE_IS_WH,
    CONF_TARIFF_TYPE,
    CONF_VAT_PERCENT,
    DOMAIN,
)

# The band edges are pro-rated by elapsed days, so the cost drifts even when
# consumption is flat. Recompute hourly in addition to on source updates.
_SCAN_INTERVAL = timedelta(hours=1)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the cost sensor from a config entry."""
    async_add_entities([EnemaltaCostSensor(entry)])


def _period_days(period_start: str | None) -> int | None:
    """Days elapsed in the current billing period (inclusive of the start)."""
    if not period_start or period_start in ("unknown", "unavailable", "none"):
        return None
    start = dt_util.parse_date(period_start)
    if start is None:
        return None
    return (dt_util.now().date() - start).days + 1


class EnemaltaCostSensor(SensorEntity):
    """Estimated Enemalta electricity cost for the current billing period."""

    _attr_has_entity_name = True
    _attr_name = "Electricity cost"
    _attr_native_unit_of_measurement = "€"
    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:cash-multiple"
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_cost"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Enemalta Tariff Cost",
            manufacturer="Enemalta (unofficial)",
            model="Pro-rata tariff calculator",
        )

    async def async_added_to_hass(self) -> None:
        source = self._entry.data[CONF_SOURCE]
        self.async_on_remove(
            async_track_state_change_event(
                self.hass, [source], self._handle_change
            )
        )
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self._handle_interval, _SCAN_INTERVAL
            )
        )

    @callback
    def _handle_change(self, _event) -> None:
        self.async_write_ha_state()

    @callback
    def _handle_interval(self, _now) -> None:
        self.async_write_ha_state()

    @property
    def _consumption_kwh(self) -> float | None:
        data = self._entry.data
        state = self.hass.states.get(data[CONF_SOURCE])
        if state is None or state.state in ("unknown", "unavailable", "none", ""):
            return None
        try:
            current = float(state.state)
        except (TypeError, ValueError):
            return None
        raw = current - float(data.get(CONF_BASELINE, 0.0))
        if data.get(CONF_SOURCE_IS_WH):
            raw = raw / 1000
        return max(raw, 0.0)

    @property
    def available(self) -> bool:
        return self._consumption_kwh is not None

    @property
    def native_value(self) -> float | None:
        data = self._entry.data
        kwh = self._consumption_kwh
        if kwh is None:
            return None
        days = _period_days(data.get(CONF_PERIOD_START)) or 1
        return calculate_cost(
            kwh=kwh,
            tariff_type=data[CONF_TARIFF_TYPE],
            phase=data[CONF_PHASE],
            residents=int(data[CONF_RESIDENTS]),
            primary=bool(data[CONF_PRIMARY]),
            include_service_charge=bool(data[CONF_INCLUDE_SERVICE_CHARGE]),
            vat_percent=float(data[CONF_VAT_PERCENT]),
            days=days,
        )

    @property
    def extra_state_attributes(self) -> dict:
        data = self._entry.data
        kwh = self._consumption_kwh
        days = _period_days(data.get(CONF_PERIOD_START))
        return {
            "tariff_type": data[CONF_TARIFF_TYPE],
            "consumption_kwh": None if kwh is None else round(kwh, 1),
            "period_start": data.get(CONF_PERIOD_START),
            "period_days": days,
            "band1_allowance_this_period": (
                None if days is None else band1_allowance(days)
            ),
            "note": (
                "Bands pro-rated to the billing period "
                "(annual_allowance/365*days). Press 'Reset billing period' when "
                "each ARMS bill period begins. Res/Dom incl 5% VAT; Non-Res excl "
                "VAT. Service charge and Eco-Reduction pro-rated by days. "
                "Estimate only — verify vs bill."
            ),
        }
