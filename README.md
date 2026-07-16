# Cosori Dual Blaze Air Fryer — Home Assistant integration

Control a **Cosori Dual Blaze 6.8qt smart air fryer** (`CAF-P583S`, including the
EU/UK `CAF-P583S-KEU`) from Home Assistant, via the VeSync cloud.

Neither Home Assistant core nor any released version of
[pyvesync](https://github.com/webdjoe/pyvesync) supports CAF-series air fryers —
support for this model was merged into pyvesync's `air-fryer-refactor` branch in
July 2026 ([PR #517](https://github.com/webdjoe/pyvesync/pull/517)) but has not
shipped in a release. This integration installs that branch (pinned to a known
commit) and exposes the fryer as proper Home Assistant entities and services.

## Features

| Entity | Type | Notes |
|---|---|---|
| Cook status | sensor | `standby`, `cooking`, `heating`, `cookStop`, `cookEnd`, … |
| Current temperature | sensor | Always °C (the device reports °C regardless of display unit) |
| Set temperature / set time / time remaining | sensor | What the fryer is currently doing |
| Cook mode | sensor | Active mode/recipe |
| Cooking | binary sensor | On while cooking/heating — great for "food's ready" notifications |
| Connectivity | binary sensor (diagnostic) | Is the fryer reachable by the VeSync cloud |
| Cook temperature | number | Pending setting, °C 80–205 in 5° steps |
| Cook minutes | number | Pending setting, 1–180 min |
| Preset | select | Manual Cook, AirFry, Broil, Roast, Bake, Reheat, Steak, Seafood, Veggies, French Fries, Frozen, Chicken |
| Start cook / Stop cook | button | Starts with the pending settings |

### Services

- `cosori_dualblaze.start_cook` — `temperature` (°C), `minutes`, optional `preset`
- `cosori_dualblaze.end_cook`

Example automation:

```yaml
alias: Preheat fryer at 6pm
triggers:
  - trigger: time
    at: "18:00:00"
actions:
  - action: cosori_dualblaze.start_cook
    data:
      temperature: 200
      minutes: 15
      preset: AirFry
```

## Installation

### HACS (recommended)

1. HACS → three-dot menu → **Custom repositories**
2. Repository: `https://github.com/benjaml4/ha-cosori-dualblaze`, category **Integration**
3. Install **Cosori Dual Blaze Air Fryer**, restart Home Assistant
4. Settings → Devices & Services → **Add Integration** → *Cosori Dual Blaze*
5. Sign in with your VeSync app credentials and your two-letter country code
   (e.g. `GB` — this routes EU/UK accounts to the correct VeSync region)

### Manual

Copy `custom_components/cosori_dualblaze/` into your Home Assistant
`config/custom_components/` directory and restart.

## Notes & limitations

- **Cloud polling only.** The fryer has no local API (it keeps a single
  outbound TLS connection to VeSync's cloud); polling is every 30 s while
  cooking, 120 s when idle.
- **No pause/resume or preheat** — the Dual Blaze protocol doesn't expose them
  remotely (physically pulling the basket pauses; reinserting resumes).
- **2FA:** if VeSync login fails with valid credentials, temporarily disable
  2FA in the VeSync app, add the integration, then re-enable it.
- **Pinned dependency:** installs
  `pyvesync @ git+https://github.com/webdjoe/pyvesync@98429e9` (the
  `air-fryer-refactor` branch). May conflict with the core `vesync`
  integration if you also run that — the two install different builds of the
  same library. Once upstream ships a release containing CAF support this will
  move to a normal PyPI pin.
- First setup takes a little longer than usual while pip clones the library.

## Credits

- [webdjoe/pyvesync](https://github.com/webdjoe/pyvesync) — the underlying library
- [RedsGT](https://github.com/RedsGT) — Dual Blaze support
  ([PR #517](https://github.com/webdjoe/pyvesync/pull/517))
- Packet captures and protocol notes from
  [pyvesync issue #477](https://github.com/webdjoe/pyvesync/issues/477)

## Disclaimer

This project starts and stops a **heating appliance**. Only automate cooks with
the basket loaded and the appliance attended. Not affiliated with Cosori or
VeSync.
