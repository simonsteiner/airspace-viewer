# Map legacy class tokens in the app, not with `normalize_legacy_classes`

`openair-rs-py` 0.2 returns the raw `AC` token as an airspace's class, while colors, the legend and labels are keyed on the class names 0.1.x returned (`"R"` was `"Restricted"`). We map tokens back in the app with `display_class()` and leave `openair`'s `normalize_legacy_classes` off, because that option raises when a legacy `AC` token disagrees with an existing `AY` type, failing the whole file, and real French files do that thousands of times.

## Consequences

- OpenAir v2 airspaces written as `AC UNC` get their display class from the `AY` type, using the same names the legacy tokens map to, so both spellings of one airspace look alike.
- A class token the app doesn't know is shown as-is in the default color instead of failing the file.
