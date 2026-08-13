"""Pure Enemalta tariff cost calculation.

This is a faithful Python port of the pro-rata band engine originally
implemented as a Jinja template in ``enemalta_tariff.yaml`` (v2.1.0).

Enemalta does NOT use a single annual cumulative band. Each bill receives a
pro-rata slice of every band's annual allowance, scaled by the number of days
in the billing period::

    period_allowance = annual_allowance / 365 * days_in_period

Rates transcribed from the official Enemalta pages:
  * Residential / Domestic pages revised 2026-02-06 (incl. 5% VAT)
  * Non-Residential page revised 2026-04-24 (excl. VAT)

INFORMATION ONLY. Verify against your ARMS bill. In any discrepancy the
Electricity Connection and Supply Regulations (S.L.545.41) prevail.
"""

from __future__ import annotations

# Band upper edges (kWh, annual) and their €/kWh rate. The final huge edge is
# an effectively-open top band.
_BANDS = {
    "Residential": (
        [(2000, 0.1047), (6000, 0.1298), (10000, 0.1607), (20000, 0.3420), (10**12, 0.6076)],
        False,  # rates already include VAT
    ),
    "Domestic": (
        [(2000, 0.1365), (6000, 0.1673), (10000, 0.2023), (20000, 0.4180), (10**12, 0.6860)],
        False,
    ),
    "Non-Residential": (
        [
            (2000, 0.1215),
            (6000, 0.1275),
            (10000, 0.1373),
            (20000, 0.1485),
            (60000, 0.1613),
            (100000, 0.1500),
            (1000000, 0.1403),
            (5000000, 0.1275),
            (10**12, 0.1080),
        ],
        True,  # rates are ex-VAT
    ),
}

# Mandatory service charge per year.
_SERVICE_CHARGE = {
    # tariff family: (single_phase, triple_phase)
    "residential": (65.0, 195.0),  # Residential + Domestic (incl. VAT)
    "non_residential": (120.0, 360.0),  # excl. VAT
}


def calculate_cost(
    kwh: float,
    tariff_type: str,
    phase: str,
    residents: int,
    primary: bool,
    include_service_charge: bool,
    vat_percent: float,
    days: int,
) -> float:
    """Return the estimated cost (€) for the billing period so far.

    ``days`` is the number of days elapsed in the current billing period
    (inclusive of the start day); ``kwh`` is consumption within that period.
    """
    days = max(int(days), 1)
    f = days / 365

    bands, apply_vat = _BANDS.get(tariff_type, _BANDS["Residential"])

    # Marginal pricing across pro-rated band edges.
    cost = 0.0
    lower = 0.0
    for edge, rate in bands:
        upper = edge * f
        if kwh > lower:
            seg = min(kwh, upper) - lower
            cost += seg * rate
            lower = upper

    # Eco-Reduction (Residential primary residence only), pro-rated by days.
    eco = 0.0
    if tariff_type == "Residential" and primary and residents >= 1:
        annual_est = kwh / days * 365
        cap = 2000 if residents == 1 else 1750 * residents
        if annual_est <= cap:
            b1 = 2000 * f
            # 25% tranche: units within the pro-rata band-1 allowance.
            eco = min(kwh, b1) * 0.1047 * 0.25
            # 15% tranche (2+ residents): units above band 1, at band-2 rate.
            if residents != 1 and kwh > b1:
                t2 = min(kwh - b1, 6000 * f - b1)
                eco += t2 * 0.1298 * 0.15

    subtotal = cost - eco

    if include_service_charge:
        family = "non_residential" if tariff_type == "Non-Residential" else "residential"
        single, triple = _SERVICE_CHARGE[family]
        sc_annual = single if phase == "Single" else triple
        subtotal += sc_annual / 365 * days

    if apply_vat:
        subtotal *= 1 + vat_percent / 100

    return round(subtotal, 2)


def band1_allowance(days: int) -> float:
    """Pro-rated band-1 allowance (kWh) for the period, for sanity checks."""
    return round(2000 / 365 * max(int(days), 1), 2)
