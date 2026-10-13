---
name: pebble-time2
description: Pebble Time 2 (emery) watchface development in C with the Pebble SDK. Covers what the official pebble-watchface skill does not - Health API (steps, heart rate), custom TTF fonts built from variable fonts, emulator and cloudpebble workflow from WSL2, and Time 2 implementation rules. Use when building, modifying, or debugging a Pebble Time 2 watchface.
---

# Pebble Time 2 Watchface

Layer on top of the official [pebble-watchface](https://github.com/coredevices/pebble-watchface-agent-skill) skill.
For the general build loop, layout math, GPath, and publishing, follow that skill. This one adds what it lacks.

## Target

- Device: Pebble Time 2 only. Platform `emery`, 200x228px color e-paper, rectangular. `targetPlatforms: ["emery"]`
- Colors: 64 (each RGB channel is 00 / 55 / AA / FF). No intermediate tones; anything else is rounded to the nearest
- Language: C with the Pebble SDK (Core Devices `pebble-tool`). Alloy (JS) is not an option: it has no HealthService
- Sensors: steps and heart rate via Health API. Compass is too inaccurate to use
- `wscript` is the SDK default and needs no edits. Resources are registered in `package.json` under `resources.media`

## Commands

```sh
pebble build                                               # build/*.pbw
pebble install --emulator emery                            # launch in emulator
pebble screenshot --no-open --emulator emery out.png       # capture, then Read the PNG to inspect
pebble emu-set-time --emulator emery "23:59:30"            # minute change / rollover (HH:MM:SS only)
pebble emu-battery --emulator emery --percent 15           # low battery state
pebble emu-bt-connection --emulator emery --connected no   # BT disconnected state
pebble emu-steps --emulator emery 12345                    # step count
pebble emu-heart-rate --emulator emery 72                  # heart rate
pebble kill && pebble wipe                                 # first thing to try when the emulator misbehaves
```

Verify every change: build → install → screenshot → Read the PNG. Adjust until it matches the spec coordinates.

### Real device (cloud relay)

WSL2 has outbound access only, so transfer goes through cloudpebble. Nothing needs to be set up on the Windows side.
Turn on Dev Connection in the phone app first.

```sh
pebble install --cloudpebble
pebble logs --cloudpebble
pebble screenshot --cloudpebble --no-open out.png
```

### Environment quirks

- `You must be logged in`: run `PYTHONUNBUFFERED=1 pebble login --no-open-browser` in the background, extract the URL
  from its output, and ask the user to open it in a browser. Without `PYTHONUNBUFFERED` the URL stays buffered and never shows
- Emulator needs `libsdl2-2.0-0 libglib2.0-0 libpixman-1-0 zlib1g libsndio7.0`. If missing, ask the user to install them with sudo

## Implementation rules

- **Tick**: `tick_timer_service_subscribe(MINUTE_UNIT, ...)`. Never keep a continuous `app_timer` running. No seconds display
- **Animation**: only on minute change, via the `Animation` API with a custom `AnimationImplementation`, 500〜800ms.
  Leave no timer behind when it ends. No animation at startup
- **Layers**: static elements (frame, rings, routes) on a background Layer, dynamic elements (time, markers, data rows)
  on a separate Layer. Partial updates call `layer_mark_dirty` on the affected Layer only.
  Static elements may also be rendered once at startup into an 8-bit `GBitmap` and blitted with `graphics_draw_bitmap_in_rect`
- **Coordinates**: take the screen size from `layer_get_bounds()`. Spec coordinates are emery constants collected in `#define`s
- **Math**: no floating point. `sin_lookup` / `cos_lookup` with `TRIG_MAX_ANGLE` / `TRIG_MAX_RATIO`, angles via `DEG_TO_TRIGANGLE`.
  12 o'clock is 0°, clockwise, same as `DEG_TO_TRIGANGLE`. Wedges use `graphics_fill_radial`; split into two calls when crossing 360°
- **No runtime randomness** in drawing. Shapes that vary per hour or minute come from lookup tables, or they flicker on every redraw
- **Fonts**: system fonts use `FONT_KEY_*` names exactly as documented. A nonexistent name or size crashes silently
- **Cleanup**: unsubscribe `tick_timer`, `health`, `connection`, `battery_state` in `deinit`. Destroy Layers and unload fonts in window unload

## Health API

```c
static bool prv_metric_accessible(HealthMetric metric) {
  time_t end = time(NULL);
  time_t start = time_start_of_today();
  return health_service_metric_accessible(metric, start, end) == HealthServiceAccessibilityMaskAvailable;
}

steps = prv_metric_accessible(HealthMetricStepCount) ? health_service_sum_today(HealthMetricStepCount) : -1;
bpm   = prv_metric_accessible(HealthMetricHeartRateBPM) ? health_service_peek_current_value(HealthMetricHeartRateBPM) : -1;
```

- Subscribe with `health_service_events_subscribe` and refresh on `HealthEventMovementUpdate` / `HealthEventHeartRateUpdate`.
  Keep the heart-rate sampling interval at the OS default
- Show `--` when a metric is unavailable or Health is disabled
- Connection: `connection_service_peek_pebble_app_connection` at startup, then `connection_service_subscribe`.
  On disconnect, one `vibes_short_pulse` and a visual change; restore on reconnect
- Battery: `battery_state_service_peek` at startup, then `battery_state_service_subscribe`. Low threshold used so far is 20%

## Custom fonts

Pebble's font converter uses only a variable font's default instance (often Thin), and ignores OpenType features such as `ss01`.
Bake static TTFs first.

1. Put the variable font under `resources/fonts/source/` and its OFL text next to it
2. Describe the instances in `resources/fonts/instances.json`:

```json
{
  "sources": {
    "outfit": { "file": "source/Outfit[wght].ttf", "glyph_substitutions": { "1": "one.ss01" } },
    "saira":  { "file": "source/Saira[wdth,wght].ttf" }
  },
  "instances": {
    "Saira-Time.ttf":   { "source": "saira",  "axes": { "wdth": 75, "wght": 800 } },
    "Outfit-Text.ttf":  { "source": "outfit", "axes": { "wght": 600 } },
    "Outfit-Value.ttf": { "source": "outfit", "axes": { "wght": 400 } }
  }
}
```

3. Copy `scripts/build-fonts.py` from this skill into the project's `scripts/` and run `uv run scripts/build-fonts.py`
4. Register each use in `package.json`. The resource name ends with the pixel size, `characterRegex` limits the glyph set
   (never include Japanese glyphs), and `compatibility: "2.7"` is required:

```json
{ "type": "font", "name": "FONT_TIME_44", "file": "fonts/Saira-Time.ttf", "characterRegex": "[0-9:]", "compatibility": "2.7" }
```

5. Load with `fonts_load_custom_font(resource_get_handle(RESOURCE_ID_FONT_TIME_44))`, unload in window unload

Letter spacing is not supported by `graphics_draw_text`; draw one character at a time with computed x positions.
`glyph_substitutions` exists because Outfit's default `1` reads as `7` at small sizes.

## References

- SDK / API: <https://developer.repebble.com>
- Official skill (templates, drawing guide, publishing): <https://github.com/coredevices/pebble-watchface-agent-skill>
