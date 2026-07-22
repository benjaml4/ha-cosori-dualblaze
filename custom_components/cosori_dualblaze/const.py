"""Constants for the Cosori Dual Blaze integration."""
from __future__ import annotations

DOMAIN = "cosori_dualblaze"

CONF_COUNTRY_CODE = "country_code"
DEFAULT_COUNTRY_CODE = "GB"

# Polling defaults (seconds) — overridable per entry via the options flow.
# Kept conservative: VeSync rate-limits / temporarily blocks accounts that
# poll too aggressively. Idle is the big lever (the fryer is idle ~24h/day),
# so it defaults high; cooking sessions are short and bounded.
CONF_SCAN_COOKING = "scan_interval_cooking"
CONF_SCAN_IDLE = "scan_interval_idle"
DEFAULT_SCAN_COOKING = 30
DEFAULT_SCAN_IDLE = 600
# Hard floor: even a hand-set option can't poll faster than this, to avoid
# tripping VeSync's abuse detection.
MIN_SCAN_SECONDS = 20
MAX_SCAN_SECONDS = 3600

# cook_status values that mean the appliance is actively heating/cooking.
RUNNING_STATUSES = {"cooking", "heating", "preheating"}

# Additional mid-cook values (paused, basket out, queued) that warrant fast
# polling even though nothing is heating.
ACTIVE_STATUSES = RUNNING_STATUSES | {"pullOut", "cookStop", "ready"}

# Temperature limits for the CAF-P583S-KEU (Celsius) model.
MIN_TEMP_C = 80
MAX_TEMP_C = 205
TEMP_STEP_C = 5
DEFAULT_TEMP_C = 200

MIN_MINUTES = 1
MAX_MINUTES = 180
DEFAULT_MINUTES = 15

MANUAL_PRESET = "Manual Cook"

# App preset recipe IDs, from packet captures shared in
# https://github.com/webdjoe/pyvesync/issues/477 — (mode string, recipe_id).
# Manual Cook maps to AirFry: the CAF-P583S-KEU firmware rejects
# mode="Custom"/recipeId=1 with code 11000000 "Invalid bypass parameter"
# (verified against real hardware, 2026-07-16).
PRESETS: dict[str, tuple[str, int]] = {
    MANUAL_PRESET: ("AirFry", 14),
    "AirFry": ("AirFry", 14),
    "Broil": ("Broil", 17),
    "Roast": ("Roast", 13),
    "Bake": ("Bake", 9),
    "Reheat": ("Reheat", 16),
    "Steak": ("Steak", 1),
    "Seafood": ("Seafood", 3),
    "Veggies": ("Veggies", 15),
    "French Fries": ("FrenchFries", 6),
    "Frozen": ("Frozen", 5),
    "Chicken": ("Chicken", 2),
}
RECIPE_TYPE = 3

SERVICE_START_COOK = "start_cook"
SERVICE_END_COOK = "end_cook"
ATTR_TEMPERATURE = "temperature"
ATTR_MINUTES = "minutes"
ATTR_PRESET = "preset"
