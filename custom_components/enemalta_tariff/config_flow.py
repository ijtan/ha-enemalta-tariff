"""Config and options flow for Enemalta Tariff Cost."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.util.dt as dt_util

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
    DEFAULT_INCLUDE_SERVICE_CHARGE,
    DEFAULT_PHASE,
    DEFAULT_PRIMARY,
    DEFAULT_RESIDENTS,
    DEFAULT_SOURCE_IS_WH,
    DEFAULT_TARIFF_TYPE,
    DEFAULT_VAT_PERCENT,
    DOMAIN,
    PHASES,
    TARIFF_TYPES,
)


def _select(options: list[str]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=options, mode=selector.SelectSelectorMode.DROPDOWN
        )
    )


def _schema(defaults: dict[str, Any], *, include_source: bool) -> vol.Schema:
    """Build the config/options schema, seeded with ``defaults``."""
    fields: dict[Any, Any] = {}
    if include_source:
        fields[vol.Required(CONF_SOURCE, default=defaults.get(CONF_SOURCE))] = (
            selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor")
            )
        )
    fields.update(
        {
            vol.Required(
                CONF_SOURCE_IS_WH,
                default=defaults.get(CONF_SOURCE_IS_WH, DEFAULT_SOURCE_IS_WH),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_TARIFF_TYPE,
                default=defaults.get(CONF_TARIFF_TYPE, DEFAULT_TARIFF_TYPE),
            ): _select(TARIFF_TYPES),
            vol.Required(
                CONF_PHASE, default=defaults.get(CONF_PHASE, DEFAULT_PHASE)
            ): _select(PHASES),
            vol.Required(
                CONF_RESIDENTS,
                default=defaults.get(CONF_RESIDENTS, DEFAULT_RESIDENTS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0, max=20, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_VAT_PERCENT,
                default=defaults.get(CONF_VAT_PERCENT, DEFAULT_VAT_PERCENT),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=25,
                    step=0.5,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="%",
                )
            ),
            vol.Required(
                CONF_PRIMARY, default=defaults.get(CONF_PRIMARY, DEFAULT_PRIMARY)
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_INCLUDE_SERVICE_CHARGE,
                default=defaults.get(
                    CONF_INCLUDE_SERVICE_CHARGE, DEFAULT_INCLUDE_SERVICE_CHARGE
                ),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_PERIOD_START,
                default=defaults.get(
                    CONF_PERIOD_START, dt_util.now().date().isoformat()
                ),
            ): selector.DateSelector(),
        }
    )
    return vol.Schema(fields)


class EnemaltaTariffConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial UI setup."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            data = dict(user_input)
            # Capture the source sensor's current reading as the period baseline
            # so consumption is measured from setup time onward.
            data[CONF_BASELINE] = _current_reading(self.hass, data[CONF_SOURCE])
            return self.async_create_entry(
                title="Enemalta Tariff Cost", data=data
            )

        return self.async_show_form(
            step_id="user", data_schema=_schema({}, include_source=True)
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return EnemaltaTariffOptionsFlow()


class EnemaltaTariffOptionsFlow(OptionsFlow):
    """Edit tariff settings after setup (without re-adding the integration)."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self.config_entry
        if user_input is not None:
            new_data = {**entry.data, **user_input}
            # Preserve the current baseline; a changed period-start date does not
            # re-baseline consumption. Use the "Reset billing period" button for
            # a clean reset when a new ARMS bill period begins.
            self.hass.config_entries.async_update_entry(entry, data=new_data)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=_schema(dict(entry.data), include_source=False),
        )


def _current_reading(hass, entity_id: str) -> float:
    """Best-effort read of the source sensor's current numeric value."""
    state = hass.states.get(entity_id)
    if state is None or state.state in ("unknown", "unavailable", "none", None, ""):
        return 0.0
    try:
        return float(state.state)
    except (TypeError, ValueError):
        return 0.0
