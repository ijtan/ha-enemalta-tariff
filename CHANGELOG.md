# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/).
Each release notes the **Enemalta tariff revision date** the rates match, so
users can tell at a glance whether a release is current.

## [Unreleased]

## [3.0.0] - 2026-08-13
### Added
- **HACS-installable custom integration** with full **UI setup** (config flow),
  in `custom_components/enemalta_tariff/`. Setup, tariff settings, and the
  billing-period start date are all configured in the UI — no YAML required.
- **Reset billing period** button entity that re-baselines consumption and sets
  the start date to today, replacing the manual `utility_meter.reset` step.
- **Options flow** to adjust tariff settings after setup, and Wh→kWh conversion
  as a config toggle.
- Root `hacs.json` and repo metadata for HACS custom-repository installation.

### Notes
- The cost engine is a faithful Python port of the v2.1.0 Jinja template;
  outputs verified identical across sample inputs. The pure-YAML package
  remains available and unchanged for those who prefer it.

## [2.1.0] - 2026-06-08
### Validated
- Full cost model checked against **four real ARMS bills** (Jun 2025 – Feb
  2026). Consumption cost, service charge and Eco-reduction now reproduce the
  billed electricity totals to within €0.01 (per-band rounding only).
- Confirmed the pro-rata divisor is **365** (not 366, even across the leap
  year) — verified to 3 decimal places against the bills' stated band units.

### Fixed
- **Eco-Reduction logic corrected** from real bills (it differs from Enemalta's
  website wording): gate on annualised consumption ≤ 1,750 × residents; apply
  25% to units within the pro-rata band-1 allowance at the band-1 rate, and 15%
  to units above that at the band-2 rate. The previous 1,000/750 pro-rata
  tranche model (all at the band-1 rate) was incorrect.

## [2.0.0] - 2026-06-08
### Changed (BREAKING — model corrected)
- **Bands are now pro-rated to the billing period, not the calendar year.**
  v1 incorrectly modelled the bands as a single annual cumulative bucket.
  Enemalta actually gives each bill a pro-rata slice of every band's annual
  allowance: `period_allowance = annual_allowance / 365 * days_in_period`.
  v1 was only correct at the very start and end of the year. (Thanks to the
  HA community forum feedback that caught this.)
- The `utility_meter` no longer uses a yearly `cycle`; you reset it manually
  when each ARMS billing period starts.

### Added
- `enemalta_period_start` datetime helper — drives the pro-rata day count.
- **Service charge** now included (mandatory, pro-rated by days): Residential/
  Domestic €65 single / €195 triple phase (incl VAT); Non-Residential €120 /
  €360 (excl VAT). Toggle + phase selector helpers added.
- Sensor attributes `period_days` and `band1_allowance_this_period` for
  transparency / verification against a real bill.

### Migration from 1.0.0
- Replace the package file. New helpers appear after restart.
- Set `enemalta_period_start` to your current bill's start date and reset the
  meter (`action: utility_meter.reset`, target
  `sensor.enemalta_period_energy`). Note the meter entity was renamed from
  `enemalta_yearly_energy` to `enemalta_period_energy`.

## [1.0.0] - 2026-06-08
### Added
- Initial release.
- Residential, Domestic and Non-Residential cumulative-band cost calculation.
- Marginal (band-by-band) pricing via a yearly `utility_meter`.
- Residential Eco-Reduction estimate (annualised pro-rata) for 1-person and
  2+-person households.
- Optional Wh→kWh converter for Tuya/LocalTuya-style sensors.
- Configurable helpers: tariff type, registered residents, primary-residence
  flag, Non-Residential VAT percent.

### Rates
- Residential & Domestic: match Enemalta pages revised **2026-02-06**.
- Non-Residential (kWh): match Enemalta page revised **2026-04-24**.

### Not included
- Fixed annual service charges.
- Maximum Demand tariff (three-phase > 60 A).
- Non-Residential day/night and kVAh sub-tariff tables.

<!--
When updating rates, copy this template:

## [x.y.z] - YYYY-MM-DD
### Changed
- Updated <Residential/Domestic/Non-Residential> band rates to match Enemalta
  page revised YYYY-MM-DD.
-->
