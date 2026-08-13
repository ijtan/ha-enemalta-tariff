# Enemalta Tariff Cost Calculator for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Calculates the running cost of your electricity consumption against
[Enemalta](https://www.enemalta.com.mt/)'s (Malta) cumulative-band tariffs —
**Residential**, **Domestic**, and **Non-Residential** — including the
residential **Eco-Reduction** estimate.

Two ways to install:

- **Custom integration (recommended)** — install via **HACS** and set it up
  entirely in the UI (config flow, no YAML). Adds an
  `sensor.*_electricity_cost` entity, a **Reset billing period** button, and an
  options screen to tweak settings. This is a fork of
  [beta-j/ha-enemalta-tariff](https://github.com/beta-j/ha-enemalta-tariff)
  that adds HACS + UI support.
- **Pure-YAML package** — the original approach (a `utility_meter` plus a
  template sensor and helpers). No custom component; works on any install and
  is easy to inspect. See [Manual YAML package](#manual-yaml-package) below.

Both use the **same** pro-rata band engine and rates.

> ⚠️ **Information only.** Every effort is made to keep the rates accurate, but
> this is an estimate. Always verify against your ARMS bill. In the event of
> any discrepancy, the *Electricity Connection and Supply Regulations
> (S.L.545.41)* and other applicable laws prevail. See [rate source &
> revision dates](#rate-source).

---

## How it works

Enemalta charges on consumption bands, but **each bill gets a pro-rata slice
of every band's annual allowance**, scaled by the number of days in that
billing period:

```
period_allowance = annual_allowance / 365 × days_in_period
```

For example, band 1's 2,000-unit annual allowance over a 59-day bill becomes
`2000 / 365 × 59 = 323.288` units at the band-1 rate for that bill. ARMS
billing cycles are **irregular** (commonly 59–70 days), so the package can't
work this out on its own — you tell it your **billing-period start date** and
**reset the meter** when each new period begins. This package:

1. Tracks consumption within the current **billing period** via a
   `utility_meter` you reset each period.
2. Pro-rates every band edge by the days elapsed, then prices **marginally**,
   band by band.
3. Adds the **mandatory service charge**, also pro-rated by days.
4. For Residential primary residences, subtracts a pro-rated **Eco-Reduction**
   estimate based on registered residents.

---

## Requirements

- A sensor that reports **cumulative** energy (a total that only climbs, e.g.
  `total_increasing`). A momentary *power* sensor (W) will **not** work
  directly — see [Wh vs kWh / power vs energy](#wh-vs-kwh--power-vs-energy).
- Units in **kWh**. If your sensor reports **Wh** (common on Tuya/LocalTuya
  plugs), enable the included converter — see below.

---

## Installation (HACS — recommended)

1. **HACS → ⋮ → Custom repositories**, add
   `https://github.com/ijtan/ha-enemalta-tariff` with category **Integration**.
2. Search HACS for **Enemalta Tariff Cost**, install it, and **restart** Home
   Assistant.
3. **Settings → Devices & Services → + Add Integration → Enemalta Tariff
   Cost**.
4. In the config dialog:
   - **Energy sensor** — pick your **cumulative** kWh sensor (a total that only
     climbs; `total_increasing`). A momentary *power* (W) sensor won't work —
     see [Wh vs kWh / power vs energy](#wh-vs-kwh--power-vs-energy).
   - **Source reads in Wh** — enable if your sensor is in Wh (common on
     Tuya/LocalTuya plugs); the integration divides by 1000.
   - Set **tariff type, phase, residents, VAT, primary residence, service
     charge**, and the **billing period start date** from your current ARMS
     bill.
5. Consumption is measured from the reading captured at setup. When each new
   ARMS bill period begins, press the **Reset billing period** button — it
   re-baselines consumption and sets the start date to today.

Change any setting later via the integration's **Configure** (⚙) button. The
`sensor.*_electricity_cost` entity exposes the same attributes as the YAML
version (`consumption_kwh`, `period_days`, `band1_allowance_this_period`, …).

---

## Manual YAML package

Prefer no custom component? Use the pure-YAML package instead.

1. Copy `enemalta_tariff.yaml` to your config:
   `<config>/packages/enemalta_tariff.yaml`
   (create the `packages` folder if it doesn't exist).

2. Enable packages in `configuration.yaml` (add under your existing
   `homeassistant:` block, don't create a second one):

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

3. Point the `utility_meter` at **your** energy sensor. In the package file,
   under `SECTION C`, change:

   ```yaml
   utility_meter:
     enemalta_period_energy:
       source: sensor.CHANGE_ME_total_energy_kwh   # <-- your kWh sensor
   ```

4. *(Optional)* If your sensor reads in **Wh**, uncomment `SECTION B` (the
   converter), set its source to your Wh sensor, and point the `utility_meter`
   `source:` at `sensor.energy_kwh_for_enemalta`.

5. **Developer Tools → YAML → Check Configuration**, then **Restart**.

6. Set the **Enemalta Billing Period Start** helper to the start date shown on
   your current ARMS bill, and reset the meter so it counts from now:

   ```yaml
   action: utility_meter.reset
   target:
     entity_id: sensor.enemalta_period_energy
   ```

   Repeat step 6 each time a new bill period begins.

---

## Configuration (helpers)

After restarting, set values under **Settings → Devices & Services → Helpers**:

| Helper | What it does |
| --- | --- |
| **Enemalta Tariff Type** | `Residential` / `Domestic` / `Non-Residential` |
| **Enemalta Registered Residents** | People registered on the ARMS service (drives Eco-Reduction) |
| **Enemalta Primary Residence** | On = eligible for Eco-Reduction |
| **Enemalta VAT Percent** | Only used for Non-Residential (rates there are ex-VAT) |
| **Enemalta Supply Phase** | `Single` / `Triple` — sets the service charge |
| **Enemalta Include Service Charge** | On = add the mandatory pro-rated service charge |
| **Enemalta Billing Period Start** | Start date of your current ARMS bill (drives pro-rata) |

Add these plus `sensor.enemalta_electricity_cost` to a dashboard
(Entities card) to see the running cost and change settings inline.

---

## Sensor output

`sensor.enemalta_electricity_cost` — estimated cost in € for the current
billing period so far. Attributes:

- `tariff_type` — active tariff
- `consumption_kwh` — kWh counted this billing period
- `period_days` — days elapsed in the current billing period
- `band1_allowance_this_period` — pro-rated band-1 allowance, for sanity-checking against a bill
- `note` — pro-rata / VAT / service-charge / Eco-Reduction caveats

---

## Wh vs kWh / power vs energy

- The bands are in **kWh**. If your sensor is in **Wh**, use the `SECTION B`
  converter (it divides by 1000). A name like "total power" in Wh is usually
  really an *energy* total — that's fine, the converter handles it.
- If your value fluctuates up **and** down, it's instantaneous **power** (W),
  not cumulative energy. You'd first need a
  [Riemann sum integration](https://www.home-assistant.io/integrations/integration/)
  to turn it into energy before feeding this package.

---

## First-run behaviour

The `utility_meter` starts counting from the moment it first runs, so right
after install it reads **0** and grows from there. Align it with your bill by
setting the **Billing Period Start** helper and resetting the meter at the
start of each ARMS billing period:

```yaml
action: utility_meter.reset
target:
  entity_id: sensor.enemalta_period_energy
```

Because the bands are pro-rated by days, the cost tracks your bill throughout
the period — not just at the endpoints.

---

## What's not (yet) included

Intentionally left out for now — PRs welcome:

- **Maximum Demand** tariff (three-phase services > 60 A) — uncommon for homes
- Non-Residential **day/night** and **kVAh** sub-tariff tables

(The mandatory service charge **is** now included, pro-rated by days.)

---

## Rate source

Rates transcribed from the official Enemalta pages:

- [Residential](https://www.enemalta.com.mt/13797-2/) — page revised 2026-02-06
- [Domestic](https://www.enemalta.com.mt/domestic-property-services/) — revised 2026-02-06
- [Non-Residential](https://www.enemalta.com.mt/non-residential-property-services/) — revised 2026-04-24

When Enemalta changes the tariffs, update the **RATES SECTION** at the top of
the package file (and the matching values in the template), then bump
`CHANGELOG.md`.

---

## Contributing

Issues and PRs welcome — especially rate updates, the omitted charges above,
and real-world testing across different meter setups. Please note which
Enemalta revision date any rate change corresponds to.

## Licence

[MIT](LICENSE). Provided as-is, with no warranty. Tariff data belongs to
Enemalta plc; this project merely reproduces it for convenience.
