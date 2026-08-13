"""Constants for the Enemalta Tariff Cost integration."""

DOMAIN = "enemalta_tariff"

# Config / options keys
CONF_SOURCE = "source_entity"
CONF_SOURCE_IS_WH = "source_is_wh"
CONF_TARIFF_TYPE = "tariff_type"
CONF_PHASE = "phase"
CONF_RESIDENTS = "residents"
CONF_VAT_PERCENT = "vat_percent"
CONF_PRIMARY = "primary_residence"
CONF_INCLUDE_SERVICE_CHARGE = "include_service_charge"
CONF_PERIOD_START = "period_start"
CONF_BASELINE = "baseline"

# Selectable options
TARIFF_TYPES = ["Residential", "Domestic", "Non-Residential"]
PHASES = ["Single", "Triple"]

# Defaults used by the config flow
DEFAULT_SOURCE_IS_WH = False
DEFAULT_TARIFF_TYPE = "Residential"
DEFAULT_PHASE = "Single"
DEFAULT_RESIDENTS = 2
DEFAULT_VAT_PERCENT = 18.0
DEFAULT_PRIMARY = True
DEFAULT_INCLUDE_SERVICE_CHARGE = True
