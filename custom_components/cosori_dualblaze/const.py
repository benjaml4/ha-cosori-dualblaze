"""Constants for the Cosori Dual Blaze integration."""
from __future__ import annotations

DOMAIN = "cosori_dualblaze"

CONF_COUNTRY_CODE = "country_code"
DEFAULT_COUNTRY_CODE = "GB"

# Polling: fast while a cook is active, slow when idle.
SCAN_INTERVAL_COOKING = 30
SCAN_INTERVAL_IDLE = 120

# cook_status values that mean the appliance is actively heating/cooking.
RUNNING_STATUSES = {"cooking", "heating", "preheating"}

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
PRESETS: dict[str, tuple[str, int]] = {
    MANUAL_PRESET: ("Custom", 1),
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
